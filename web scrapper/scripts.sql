CREATE TABLE redbus.bus_routes1 (
  id INT NOT NULL AUTO_INCREMENT,
  route_name TEXT NOT NULL,
  route_link TEXT NOT NULL,
  bus_name TEXT NOT NULL,
  bus_type TEXT NOT NULL,
  depart_time TEXT NOT NULL,
  duration TEXT NOT NULL,
  arrival_time TEXT NOT NULL,
  rating FLOAT NULL,
  price DECIMAL NOT NULL,
  seats_available INT NOT NULL,
  depart_loc TEXT NULL,
  arrival_loc TEXT NULL,
  PRIMARY KEY (id));