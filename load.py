import duckdb

#linked to the database file
con = duckdb.connect("ecom.duckdb")

#store raw data into a table
con.sql("""
    CREATE OR REPLACE TABLE raw AS
    SELECT * FROM read_csv_auto('2019-Nov.csv')
""")

print("Finished loading data into the database.")
con.close()
