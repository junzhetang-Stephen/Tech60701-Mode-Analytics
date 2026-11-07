#!/usr/bin/env python
# coding: utf-8

# In[3]:


import pyodbc

# Nom de votre serveur
server = r"DESKTOP-RRT65BQ\SQLEXPRESS"
database = (
    "TIA"  # Remplacez par le nom de votre base de données
)

try:
  # Connexion avec l'authentification Windows
  conn = pyodbc.connect(
      f"DRIVER={{ODBC Driver 17 for SQL Server}};"
      f"SERVER={server};"
      f"DATABASE={database};"
      f"Trusted_Connection=yes;"
  )
  print("Super ! Connexion à la base de données réussie !")

  # Fermer la connexion
  conn.close()

except Exception as e:
  # Capturer et afficher les informations d'erreur
  print(f"Échec de la connexion. Raison de l'erreur : {e}")


# In[8]:


import pyodbc
import pandas as pd

# =====================================
# 1. Connect to AdventureWorks2025
# =====================================

server = r"DESKTOP-RRT65BQ\SQLEXPRESS"
database = "AdventureWorks2025"

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=yes;"
)

print("Successfully connected to:", database)

# =====================================
# 2. Extract all tables
# =====================================

cursor = conn.cursor()

cursor.execute("""
SELECT
    s.name AS SchemaName,
    t.name AS TableName,
    SUM(p.rows) AS TotalRows
FROM sys.tables AS t
INNER JOIN sys.schemas AS s
    ON t.schema_id = s.schema_id
INNER JOIN sys.partitions AS p
    ON t.object_id = p.object_id
WHERE p.index_id IN (0, 1)
GROUP BY
    s.name,
    t.name
ORDER BY
    s.name,
    t.name;
""")

tables = pd.DataFrame.from_records(
    cursor.fetchall(),
    columns=[col[0] for col in cursor.description]
)

print("\n========== ALL TABLES ==========")
print(tables.to_string(index=False))

print("\nTotal number of tables:", len(tables))

# =====================================
# 3. Extract all columns
# =====================================

cursor.execute("""
SELECT
    s.name AS SchemaName,
    t.name AS TableName,
    c.name AS ColumnName,
    ty.name AS DataType,
    c.max_length AS MaxLength,
    c.is_nullable AS IsNullable
FROM sys.tables AS t
INNER JOIN sys.schemas AS s
    ON t.schema_id = s.schema_id
INNER JOIN sys.columns AS c
    ON t.object_id = c.object_id
INNER JOIN sys.types AS ty
    ON c.user_type_id = ty.user_type_id
ORDER BY
    s.name,
    t.name,
    c.column_id;
""")

columns = pd.DataFrame.from_records(
    cursor.fetchall(),
    columns=[col[0] for col in cursor.description]
)

print("\n========== ALL COLUMNS ==========")
print(columns.to_string(index=False))

# =====================================
# 4. Save metadata
# =====================================

tables.to_csv(
    "database_tables.csv",
    index=False,
    encoding="utf-8-sig"
)

columns.to_csv(
    "database_columns.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nMetadata extraction completed!")



# In[ ]:




