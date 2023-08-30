# Import the dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from datetime import datetime, timedelta
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station= Base.classes.station
# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the JSON representation of precipitation data for the last 12 months."""
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    # Calculate the date one year from the last date in the dataset
    one_year_ago = datetime.strptime(most_recent_date, '%Y-%m-%d') - timedelta(days=365)
    
    # Query the precipitation data for the last 12 months
    results = session.query(Measurement.date, Measurement.prcp)\
        .filter(Measurement.date >= one_year_ago)\
        .all()
    session.close()
    # Convert the results to a dictionary
    precipitation_data = {date: prcp for date, prcp in results}
    
    return jsonify(precipitation_data)


@app.route("/api/v1.0/stations")
def station_names():
    """Return a JSON list of stations from the dataset."""
    # Query the stations
    results = session.query(Station.station).all()
    session.close()
    # Convert the results to a list
    stations_list = list(np.ravel(results))
    
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return a JSON list of temperature observations for the most active station for the last 12 months."""
    active_stations = session.query(Measurement.station, func.count(Measurement.station)) \
        .group_by(Measurement.station) \
        .order_by(func.count(Measurement.station).desc()) \
        .all()
    most_active_station = active_stations[0][0]
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = datetime.strptime(most_recent_date, '%Y-%m-%d') - timedelta(days=365)
    # Query the temperature observations for the most active station
    results = session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.station == most_active_station)\
        .filter(Measurement.date >= one_year_ago)\
        .all()
    session.close()
    # Convert the results to a list of dictionaries
    tobs_data = [{"date": date, "tobs": tobs} for date, tobs in results]
    
    return jsonify(tobs_data)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start, end=None):
    """Return a JSON list of the minimum, average, and maximum temperature for the specified date range."""
    # Query the temperature data based on the provided start and end dates
    if end:
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
            .filter(Measurement.date >= start)\
            .filter(Measurement.date <= end)\
            .all()
    else:
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
            .filter(Measurement.date >= start)\
            .all()
    session.close()
    # Convert the results to a list of dictionaries
    temperature_range_data = [{"TMIN": tmin, "TAVG": tavg, "TMAX": tmax} for tmin, tavg, tmax in results]

    return jsonify(temperature_range_data)

if __name__ == '__main__':
    app.run(debug=True)