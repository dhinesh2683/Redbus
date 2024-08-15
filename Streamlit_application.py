import streamlit as st
import pymysql
import pandas as pd

# Database connection function
def get_connection():
    return pymysql.connect(
        host='127.0.0.1',
        user='root',
        passwd='dhinesh',
        db='redbus'
    )

# Fetch data from the database
def load_data():
    conn = get_connection()
    query = "SELECT * FROM bus_info"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Main Streamlit app
def main():
    st.set_page_config(page_title="Redbus Routes Analysis", page_icon="🚌")

    # Custom CSS for styling
    st.markdown("""
        <style>
        .title {
            font-size: 2.5em;
            color: #C8102E; /* Redbus color */
            font-weight: bold;
            text-align: center;
            padding-top: 20px;
        }
        .subheader {
            color: #0066CC; /* Custom color for subheaders */
        }
        .dataframe {
            color: #333333;
            font-size: 14px;
        }
        .sidebar .sidebar-content {
            background-color: rgba(244, 244, 244, 0.8); /* Semi-transparent background for sidebar */
        }
        .key-insights {
            color: #333333; /* Dark grey text */
            font-size: 1.1em;
            margin-bottom: 20px;
        }
        .key-insights ul {
            list-style-type: disc;
            margin-left: 20px;
        }
        .key-insights li {
            margin-bottom: 10px;
        }
        .quote {
            color: #C8102E; /* Redbus color */
            font-weight: bold;
            font-size: 1.2em;
            border: 1px solid #C8102E; /* Border to make it stand out */
            padding: 10px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="title">Redbus Routes Data Filtering and Analysis</div>', unsafe_allow_html=True)

    # Load data
    df = load_data()

    # Initialize session state for filters if not already set
    if 'bus_types' not in st.session_state:
        st.session_state.bus_types = []
    if 'routes' not in st.session_state:
        st.session_state.routes = []
    if 'price_range' not in st.session_state:
        st.session_state.price_range = (float(df['price'].min()), float(df['price'].max()))
    if 'rating_range' not in st.session_state:
        st.session_state.rating_range = (float(df['star_rating'].min()), float(df['star_rating'].max()))
    if 'seat_availability_range' not in st.session_state:
        st.session_state.seat_availability_range = (int(df['seat_available'].min()), int(df['seat_available'].max()))

    # Filter widgets
    st.session_state.bus_types = st.multiselect(
        "Select Bus Type:",
        options=df['bustype'].unique(),
        default=st.session_state.bus_types
    )
    
    st.session_state.routes = st.multiselect(
        "Select Route:",
        options=df['route_name'].unique(),
        default=st.session_state.routes
    )
    
    st.session_state.price_range = st.slider(
        "Select Price Range:",
        min_value=float(df['price'].min()),
        max_value=float(df['price'].max()),
        value=st.session_state.price_range
    )
    
    st.session_state.rating_range = st.slider(
        "Select Star Rating Range:",
        min_value=float(df['star_rating'].min()),
        max_value=float(df['star_rating'].max()),
        value=st.session_state.rating_range
    )
    
    st.session_state.seat_availability_range = st.slider(
        "Select Seat Availability Range:",
        min_value=int(df['seat_available'].min()),
        max_value=int(df['seat_available'].max()),
        value=st.session_state.seat_availability_range
    )

    # Option to view full data
    if st.checkbox("Show Full Data"):
        st.subheader("Full Data:")
        st.dataframe(df.style.set_properties(**{'background-color': 'lightgrey', 'color': 'black'}), use_container_width=True)  # Simple styling

    # Check if any filters are applied
    filters_applied = (st.session_state.bus_types or st.session_state.routes or
                       (st.session_state.price_range[0] != df['price'].min() or st.session_state.price_range[1] != df['price'].max()) or
                       (st.session_state.rating_range[0] != df['star_rating'].min() or st.session_state.rating_range[1] != df['star_rating'].max()) or
                       (st.session_state.seat_availability_range[0] != df['seat_available'].min() or st.session_state.seat_availability_range[1] != df['seat_available'].max()))

    # Filter the data based on selections if filters are applied
    if filters_applied:
        filtered_data = df[
            (df['bustype'].isin(st.session_state.bus_types) if st.session_state.bus_types else True) &
            (df['route_name'].isin(st.session_state.routes) if st.session_state.routes else True) &
            (df['price'].between(st.session_state.price_range[0], st.session_state.price_range[1])) &
            (df['star_rating'].between(st.session_state.rating_range[0], st.session_state.rating_range[1])) &
            (df['seat_available'].between(st.session_state.seat_availability_range[0], st.session_state.seat_availability_range[1]))
        ]

        # Display filtered data
        st.subheader("Filtered Data:")
        st.dataframe(
            filtered_data.style.applymap(lambda x: 'background-color: lightblue' if pd.notnull(x) else '',
                                         subset=['bustype', 'route_name', 'price', 'star_rating', 'seat_available'])
                         .set_properties(**{'color': 'black'}),
            use_container_width=True
        )  # Colorful styling

        # Provide download option for the filtered data
        st.download_button(
            label="Download Filtered Data",
            data=filtered_data.to_csv(index=False),
            file_name='filtered_data.csv',
            mime='text/csv'
        )
    else:
        st.subheader("Filtered Data:")
        st.write("No filters applied. Please select some filters to see the data.")

    # Sidebar content
    st.sidebar.markdown("""
        <div class="key-insights">
            <h3>Key Insights:</h3>
            <ul>
                <li><strong>Web Scraping:</strong> Gather data from various sources to provide comprehensive insights.</li>
                <li><strong>Data Cleaning:</strong> Process raw data to ensure accuracy and consistency.</li>
                <li><strong>SQL:</strong> Use SQL queries for efficient data retrieval and manipulation.</li>
                <li><strong>Final Output:</strong> Present clean and insightful data to users.</li>
            </ul>
        </div>
        <div class="quote">
            "Travel is the only thing you buy that makes you richer."
        </div>
    """, unsafe_allow_html=True)

    
    # st.sidebar.image('images.png', width=200)

if __name__ == "__main__":
    main()
