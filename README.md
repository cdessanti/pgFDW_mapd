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

... coming soon
