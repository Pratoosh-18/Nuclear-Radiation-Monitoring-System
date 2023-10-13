import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import geocoder
import folium
from streamlit_folium import folium_static
from plyer import notification

user_latitude, user_longitude = None, None

st.title('Nuclear Power Plant Analysis')

# Upload their dataset
uploaded_file = st.file_uploader("Upload your dataset (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Display the dataset
    st.write("Uploaded Dataset:")
    st.write(df)

    # Handle missing values by filling them with 0
    df.fillna(0, inplace=True)

    # Calculate 'Safety' column based on 'Age' column
    def calculate_safety(age):
        if pd.isna(age):
            return 'Unknown'
        if age < 15:
            return 'Safe'
        elif 20 <= age < 40:
            return 'Moderate'
        else:
            return 'Dangerous'

    # Applying the safety calculation function to each row and create the 'Safety' column
    df['Safety'] = df['Age'].apply(calculate_safety)

    # Fuction to Update user's location
    def update_user_location():
        global user_latitude, user_longitude
        try:
            user_location = geocoder.ip('me')
            user_latitude, user_longitude = user_location.latlng
        except AttributeError:
            user_latitude, user_longitude = None, None

    # Update user's location
    update_user_location()

    # Create map
    st.subheader('Geographical Data Map')
    map = folium.Map(location=[user_latitude or 0, user_longitude or 0], zoom_start=10)

    # Define colors for radius circles based on safety levels
    colors = {
        'Safe': 'green',
        'Dangerous': 'purple',
        'Moderate': 'red'
    }

    dangerous_zones = []

    for index, row in df.iterrows():
        reactor_safety = row['Safety']
        if reactor_safety == 'Safe' or 'Moderate' or 'Dangerous':
            plant_latitude, plant_longitude = row['Latitude'], row['Longitude']
            
            # Distance between user and nuclear power plant in km
            distance = geodesic((user_latitude, user_longitude), (plant_latitude, plant_longitude)).km
            
            # Distance in km for alerting the user
            threshold_distance = 500
            if distance <= threshold_distance:
                dangerous_zones.append(row['Name'])

        color = colors.get(reactor_safety, 'blue')
        folium.Circle(
            location=[row['Latitude'], row['Longitude']],
            
            # Radius in meters
            radius=10000,  
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=1,
            tooltip=row['Name']
        ).add_to(map)

    # User location on the map
    folium.Marker(
        location=[user_latitude or 0, user_longitude or 0],
        icon=folium.CustomIcon(icon_image="https://cdn.iconscout.com/icon/premium/png-256-thumb/map-pointer-9-648635.png", icon_size=(32, 32))
    ).add_to(map)
    
    # Desktop notification
    
    def show_notification(plant_names):
        title = "Nuclear Radiation Proximity Alert!"
        message = f"You are near {', '.join(plant_names)} Nuclear Power Plant (Reactors).This area may be exposed to Nuclear Radiations. Long exposure to these radiations may affect your health. Please make sure that you move out from this area soon for your safety."
        notification.notify(
            title=title,
            message=message,
            app_name='Nuclear Power Plant Alert',
            timeout=10
        )

    if dangerous_zones:
        alert_message = f"You are near {', '.join(dangerous_zones)} Nuclear Power Plant (Reactors).This area may be exposed to Nuclear Radiations. Long exposure to these radiations may affect your health. Please make sure that you move out from this area soon for your safety"
        st.error(alert_message)
        # Show desktop notification if dangerous zones are detected
        show_notification(dangerous_zones)
    else:
        st.success("You are in a safe zone. No dangerous nuclear power plants nearby.")

    # Render the map
    folium_static(map) 