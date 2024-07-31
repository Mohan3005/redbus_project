import mysql.connector
import streamlit as st
import pandas as pd
import random
import string
from datetime import datetime, timedelta

def setup_database():
    conn = mysql.connector.connect(
        host="localhost",  
        user="root",  
        password="1234", 
        database="redbus_data"  
    )
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS bus_routes
                (id INT AUTO_INCREMENT PRIMARY KEY,
                route_name VARCHAR(255),
                route_link VARCHAR(255),
                busname VARCHAR(255),
                bustype VARCHAR(50),
                departing_time VARCHAR(10),
                duration VARCHAR(50),
                reaching_time VARCHAR(10),
                star_rating FLOAT,
                price DECIMAL(10, 2),
                seats_available INT,
                is_government BOOLEAN)''')
    
    conn.commit()
    return conn, c

def generate_tracking_link():
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(7))
    return f"https://b.redbus.com/{random_string}"

def insert_sample_data(conn, c):
    c.execute("SELECT COUNT(*) FROM bus_routes")
    if c.fetchone()[0] > 0:
        return  # Data already exists, no need to insert

    routes = {
    "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    "Karnataka": ["Bangalore", "Mysore", "Hubli"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur"],
    "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur"]
    }
    bus_types = ["AC", "Non-AC", "Seater", "Sleeper"]
    bus_operators = ["RedBus Express", "City Link", "Comfort Travels", "SpeedLine"]

    for _ in range(10):  # Insert 10 sample records
        state = random.choice(list(routes.keys()))
        from_city, to_city = random.sample(routes[state], 2)
        route = f"{from_city} to {to_city}"
        busname = random.choice(bus_operators)
        bustype = random.choice(bus_types)
        departing_time = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"
        duration = f"{random.randint(2, 8)} hours"
        reaching_time = (datetime.strptime(departing_time, "%H:%M") + timedelta(hours=random.randint(2, 8))).strftime("%H:%M")
        star_rating = round(random.uniform(1, 5), 1)
        price = random.randint(500, 2000)
        seats_available = random.randint(0, 40)
        is_government = random.choice([0, 1])

        route_link = f"https://www.redbus.in/bus-tickets/{from_city.lower()}-to-{to_city.lower()}-buses"

        c.execute('''INSERT INTO bus_routes 
                    (route_name, route_link, busname, bustype, departing_time, duration, reaching_time, star_rating, price, seats_available, is_government)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (route, route_link, busname, bustype, departing_time, duration, reaching_time, star_rating, price, seats_available, is_government))
    
    conn.commit()

def get_column_names(conn):
    c = conn.cursor()
    c.execute("SHOW COLUMNS FROM bus_routes")
    return [column[0] for column in c.fetchall()]

def streamlit_app():
    st.title("Redbus Data Viewer")

    conn, c = setup_database()
    insert_sample_data(conn, c)

    c.execute("SELECT COUNT(*) FROM bus_routes")
    total_records = c.fetchone()[0]
    st.sidebar.write(f"Total records in database: {total_records}")

    st.sidebar.header("Filters")
    c.execute("SELECT DISTINCT route_name FROM bus_routes")
    routes = [route[0] for route in c.fetchall()]
    selected_route = st.sidebar.selectbox("Select Route", ["All"] + routes)

    c.execute("SELECT DISTINCT bustype FROM bus_routes")
    bus_types = [bt[0] for bt in c.fetchall()]
    selected_bustypes = st.sidebar.multiselect("Select Bus Types", bus_types, default=bus_types)

    c.execute("SELECT MIN(price), MAX(price) FROM bus_routes")
    min_price, max_price = c.fetchone()
    price_range = st.sidebar.slider("Price Range", float(min_price), float(max_price), (float(min_price), float(max_price)))

    min_star_rating = st.sidebar.selectbox("Minimum Star Rating", [1, 2, 3, 4, 5])

    availability_options = ["All", "Available", "Not Available"]
    availability = st.sidebar.selectbox("Seat Availability", availability_options)

    bus_category = st.sidebar.radio("Bus Category", ["All", "Government", "Private"])

    query = "SELECT * FROM bus_routes WHERE 1=1"
    params = []
    if selected_route != "All":
        query += " AND route_name = %s"
        params.append(selected_route)

    if selected_bustypes:
        query += " AND bustype IN ({})".format(','.join(['%s'] * len(selected_bustypes)))
        params.extend(selected_bustypes)

    query += " AND price BETWEEN %s AND %s"
    params.extend(price_range)
    query += " AND star_rating >= %s"
    params.append(min_star_rating)
    if availability == "Available":
        query += " AND seats_available > 0"
    elif availability == "Not Available":
        query += " AND seats_available = 0"

    if bus_category == "Government":
        query += " AND is_government = 1"
    elif bus_category == "Private":
        query += " AND is_government = 0"

    st.sidebar.write("Debug - SQL Query:", query)
    st.sidebar.write("Debug - Query Parameters:", params)

    c.execute(query, params)
    data = c.fetchall()

    if data:
        columns = get_column_names(conn)
        df = pd.DataFrame(data, columns=columns)

        st.subheader("Bus Data")
        st.dataframe(df)

        st.subheader("Detailed Bus Information")
        for index, row in df.iterrows():
            with st.expander(f"Bus {index + 1}: {row['busname']} - {row['route_name']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Bus Name: {row['busname']}")
                    st.write(f"Bus Type: {row['bustype']}")
                    st.write(f"Departing Time: {row['departing_time']}")
                    st.write(f"Duration: {row['duration']}")
                    st.write(f"Reaching Time: {row['reaching_time']}")
                with col2:
                    st.write(f"Star Rating: {row['star_rating']}")
                    st.write(f"Price: ₹{row['price']:.2f}")
                    st.write(f"Seats Available: {row['seats_available']}")
                    st.write(f"Government Bus: {'Yes' if row['is_government'] else 'No'}")
                    st.write(f"Route Link: ")
                    link_text = f'<a href="{row["route_link"]}" target="_blank">https://www.redbus.in</a>'
                    st.markdown(link_text, unsafe_allow_html=True)
        
        st.subheader("Statistics")
        st.write(f"Total buses: {len(df)}")
        st.write(f"Average price: ₹{df['price'].mean():.2f}")
        st.write(f"Most common bus type: {df['bustype'].mode().values[0]}")

        govt_buses = df[df['is_government'] == 1]
        private_buses = df[df['is_government'] == 0]
        st.write(f"Government buses: {len(govt_buses)}")
        st.write(f"Private buses: {len(private_buses)}")
    else:
        st.write("No data available for the selected filters.")

    conn.close()

if __name__ == "__main__":
    streamlit_app()