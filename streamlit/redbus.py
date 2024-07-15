import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Redbus",
    layout="wide"
)
st.title("GUVI-Redbus Data Scraping Project Demo")

#Get the db connection details from secrets & cache the connection to avoid multiple connections
@st.cache_resource
def dbConnection():
    """Establishes a database connection using cached credentials.
    Caches the connection to avoid redundant connections.
    Returns:
        A pymysql connection object.
    """
    con = pymysql.connect(host=st.secrets.db_credentials.host, 
            user=st.secrets.db_credentials.user,  
            password = st.secrets.db_credentials.password, 
            db=st.secrets.db_credentials.db, 
            ) 
    return con

#Get distinct routes and cache the same. No need to fetch this everytime page (re)loads
@st.cache_data
def loadRoutes():
    """Loads distinct route names from the db. Caches the output as the data doesn't change """
    df = pd.read_sql_query("select distinct(route_name) from bus_routes1 order by route_name",con=dbConnection())
    return df

@st.cache_data
# values for dept time filter
def getDeptTimes():
    """Values for Departure Time filter """
    return ["Before 6am","Before 6am - 12pm","Before 12pm - 6pm","After 6pm"]

@st.cache_data
#values for bus Types
def getBusTypes():
    """Values for Bus type filter"""
    return ["Seater","Sleeper","A/C","Non A/C"]

@st.cache_data
#values for ratings
def getRatings():
    """Values for Ratings filter"""
    return [":star::star::star::star:",":star::star::star:",":star::star:","Any"]

#load unique routes to session state
if 'routes' not in st.session_state:
    st.session_state.routes = loadRoutes()

#configure filters on the sidebar
with st.sidebar:    
    st.title("Filters")
    sbRoutes = st.selectbox('Routes',
        options=st.session_state.routes['route_name'],
        index=None,
        placeholder="Select a route...",
    )
    st.divider()
    st.write('Departure Time')
    cbDeptBeforeSix = st.checkbox(getDeptTimes()[0])
    cbDeptMorning = st.checkbox(getDeptTimes()[1])
    cbDeptEvening = st.checkbox(getDeptTimes()[2])
    cbDeptNight = st.checkbox(getDeptTimes()[3])
    deptTimes = [cbDeptBeforeSix,cbDeptMorning,cbDeptEvening,cbDeptNight]
    st.divider()
    st.write('Bus Type')
    cbSeater = st.checkbox(getBusTypes()[0])
    cbSleeper = st.checkbox(getBusTypes()[1])
    cbAC = st.checkbox(getBusTypes()[2])
    cbNonAC = st.checkbox(getBusTypes()[3])
    busTypes = [cbSeater,cbSleeper,cbAC,cbNonAC]
    st.divider()
    rdRatings = st.radio(
            "Ratings",
            getRatings(),
            index=None
            )
    st.divider()
    # st.button('Reset')

# Load data for the selected filters and show the dataframe
def refreshMainTable(pRouteName, pDeptTimes, pBusTypes, pRating):
    """Fetches bus data based on selected filters and displays it in a Streamlit dataframe.

    Args:
        pRouteName: The selected route.
        pDeptTimes: A list of booleans indicating selected departure time filters.
        pBusTypes: A list of booleans indicating selected bus type filters.
        pRating: The selected rating.
    """
    try:
        deptQry = ["depart_time < '06:00'","(depart_time >= '06:00' and depart_time < '12:00')","(depart_time >= '12:00' and depart_time > '18:00')","(depart_time >= '18:00')"]
        seatQry = ["lower(bus_type) like '%seater%' ","lower(bus_type) like '%sleeper%'"]
        ratingValues = [4,3,2,0]
        if pRouteName is None:
            return
        
        #form the query based on inputs 
        #base query
        query = f"select bus_name as 'Bus Name', bus_type as 'Bus Type', depart_time as 'Departure', duration as 'Travel Time', arrival_time as 'Arrival Time', " \
            f" rating as 'Rating', price as 'Price', seats_available as 'Seats Available' from bus_routes1 where  route_name = \"{pRouteName}\" "

        #dept time filter
        first = True
        for i in range(len(pDeptTimes)):
            if pDeptTimes[i] == True:
                if first: 
                    query += f" and ( {deptQry[i]} "
                    first = False
                else: # add or condition
                    query += f" or {deptQry[i]} "
        if first == False: #added dept filter, close it with )
            query += " ) "
            
        #seater or sleeper filter
        first = True
        for i in range(2):
            if pBusTypes[i] == True:
                if first: 
                    query += f" and ( {seatQry[i]} "
                    first = False
                else: # add or condition
                    query += f" or {seatQry[i]} "
        if first == False: #added dept filter, close it with )
            query += " ) "

        #a/c or non a/c
        # if AC alone is seleted or Non A/C alone is selected then add condition. if both are selected, no need to add any condition
        if pBusTypes[2] !=  pBusTypes[3]: #either one is selected
            if pBusTypes[2] == True: #AC selected
                query += f" and lower(bus_type) not like '%non%' "
            else:
                query += f" and lower(bus_type) like '%non%' "

        #ratings filter
        if pRating != None:
            query += f" and rating >= {ratingValues[getRatings().index(pRating)]} "

        #default sort
            query += f" order by depart_time "

        #st.write(query)

        #execute sql and write dataframe
        df = pd.read_sql_query(query,con=dbConnection())
        st.header(f"{pRouteName} - {df.shape[0]} Buses found")
        st.dataframe(df)
    except Exception as e:
        print('Error :', e)

#Refresh data for the selected filters
refreshMainTable(sbRoutes,deptTimes,busTypes,rdRatings)