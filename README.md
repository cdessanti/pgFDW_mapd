# pgFDW_mapd
PostgreSQL Foreign Data Wrapper for MAPD

## Requirements
* PostgreSQL 9.3+
* PostgreSQL development packages (postgresql-server-dev-9.x)
* Mapd 3.2, 3.3 (using up to date version is recommended)
    
## Features (or lack of...)
* Simple queries with filtering on mapped tables
* You can define a view with an option called query on mapped table
    
### install Multicorn
```bash
sudo pgxn install multicorn
```
### install Mapd python driver and dependecies
```bash
sudo easy_install pip
sudo pip install pymapd
```
### clone repository
```bash
git clone https://github.com/cdessanti/pgFDW_mapd.git
```
### install FDW
```bash
cd pgFDW_mapd
python setup.py install
```

## how to use the TDW

connect to postgres and switch to your database

### create multicorn extension
```sql
CREATE EXTENSION multicorn
```

### create server to access Mapd database
```sql
CREATE SERVER fdw_mapd FOREIGN DATA WRAPPER multicorn
OPTIONS (
    wrapper 'pgFDW_mapd.pgFDW_mapd',
    host 'the_ip_or_name_of_host_hosing_mapd',  -- optional it will default to localhost (127.0.0.1)
    port 'the_port_where_mapd_is_listening',    -- tipically 9091 it will default to 9091
    user 'username',                            -- optional it will default to 'mapd'
    password 'username password'                -- optionalit will default to 'HyperInteractive'
);
```

### create foreign table definition
```sql
CREATE FOREIGN TABLE ft_flights_2008_10k
(
    flight_year         SMALLINT,
    flight_month        SMALLINT,
    flight_dayofmonth   SMALLINT,
    uniquecarrier       TEXT,
    arrdelay            SMALLINT,
    depdelay            SMALLINT,
    origin              TEXT,
    dest                TEXT
)
SERVER fdw_mapd 
OPTIONS
(
    table_name 'flights_2008_10k',  -- name of the table on remote database required
    query 'select ...' -- optional if specified the query specified will be used as an inline view
    limit 'number_of_rows' -- optional this parameter will limit the number of rows returned by FT will default is 100000
)
```

### query the foreign table
```sql
SELECT * 
FROM ft_flights_2008_10k 
WHERE origin= 'AMA' 
AND flight_dayofmonth=6  
```

### limitations
All limitations of multicorn comes with this wrapper, so group by, having, join and aggregates are not pushed to remote database and will be performed by local postgres database.

To mitigate limitations and fully exploit the performance of Mapd database you can use 'query' option while defining foreign table to perform joins, aggregates, complex filtering and so one; you can see this option as a way to define a logical view on local database, the projection and filtering will be applied to optional query.

here is an example which query will be pushed to remote database while using 'query' option

```sql
CREATE FOREIGN TABLE ft_flights_avgs
(
    flight_year         SMALLINT,
    flight_month        SMALLINT,
    origin              TEXT,
    avg_depdelay        REAL,
    avg_arrdelay        REAL
) SERVER fdw_mapd 
OPTIONS
(   table_name 'flights_2008_10k',
    query 'select flight_year,flight_month,origin,avg(arrdelay) avg_arrdelay,avg(depdelay) avg_depdelay from flights_2008_10k group by 1,2,3' 
)
```

the following query
```sql
SELECT * FROM ft_flights_avgs where origin = 'SAT' and flight_year = 2008
```
will be rewriteen and sent to Mapd this way

```sql
SELECT flight_year,flight_month,origin,avg_depdelay,avg_arrdelay 
FROM (SELECT flight_year,flight_month,origin,avg(arrdelay) avg_arrdelay,avg(depdelay) avg_depdelay 
        FROM flights_2008_10k 
        GROUP BY 1,2,3)
WHERE origin = 'SAT'
AND year = 2008
```

so you will get the aggregated and filtered data 

You can get a similar result while defining a view on target database, but i think this implementation is more flexible because you can create , modify and drop those views on client side

