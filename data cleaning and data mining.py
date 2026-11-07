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



# In[9]:


import pyodbc
import pandas as pd

# 1. Connect to AdventureWorks2025
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-RRT65BQ\\SQLEXPRESS;"
    "DATABASE=AdventureWorks2025;"
    "Trusted_Connection=yes;"
)

# 2. Check order status distribution
query_status = """
SELECT
    Status,
    COUNT(*) AS NumberOfOrders
FROM Sales.SalesOrderHeader
GROUP BY Status
ORDER BY Status;
"""

cursor = conn.cursor()
cursor.execute(query_status)

status_data = cursor.fetchall()

df_status = pd.DataFrame.from_records(
    status_data,
    columns=["Status", "NumberOfOrders"]
)

print("Order Status Distribution:")
display(df_status)


# In[10]:


# Extract Customer table
query_customer = """
SELECT *
FROM Sales.Customer;
"""

cursor.execute(query_customer)

customer_data = cursor.fetchall()

df_customer = pd.DataFrame.from_records(
    customer_data,
    columns=[column[0] for column in cursor.description]
)

# Extract SalesOrderHeader table
query_orders = """
SELECT *
FROM Sales.SalesOrderHeader;
"""

cursor.execute(query_orders)

order_data = cursor.fetchall()

df_orders = pd.DataFrame.from_records(
    order_data,
    columns=[column[0] for column in cursor.description]
)

# Basic information
print("Customer dataset:", df_customer.shape)
print("Order dataset:", df_orders.shape)

# Missing values
print("\nCustomer missing values:")
display(df_customer.isnull().sum())

print("\nOrder missing values:")
display(df_orders.isnull().sum())

# Duplicate records
print("\nCustomer duplicate rows:", df_customer.duplicated().sum())
print("Order duplicate rows:", df_orders.duplicated().sum())


# In[11]:


# 1. Convert OrderDate to datetime
df_orders["OrderDate"] = pd.to_datetime(df_orders["OrderDate"])

# 2. Define the reference date
reference_date = df_orders["OrderDate"].max() + pd.Timedelta(days=1)

# 3. Calculate RFM features
df_rfm = df_orders.groupby("CustomerID").agg(
    Recency=("OrderDate", lambda x: (reference_date - x.max()).days),
    Frequency=("SalesOrderID", "count"),
    Monetary=("TotalDue", "sum"),
    AverageOrderValue=("TotalDue", "mean")
).reset_index()

# 4. Add customer territory information
df_rfm = df_rfm.merge(
    df_customer[["CustomerID", "TerritoryID"]],
    on="CustomerID",
    how="left"
)

# 5. Inspect the new dataset
print("RFM dataset shape:", df_rfm.shape)

print("\nFirst 5 rows:")
display(df_rfm.head())

print("\nMissing values:")
display(df_rfm.isnull().sum())

print("\nDescriptive statistics:")
display(df_rfm.describe())


# In[12]:


# 1. Check data types
print("Data types:")
display(df_rfm.dtypes)

# 2. Check missing values
print("\nMissing values:")
display(df_rfm.isnull().sum())

# 3. Descriptive statistics
print("\nDescriptive statistics:")
display(df_rfm.describe())

# 4. Check unique customers
print("\nNumber of unique customers:")
print(df_rfm["CustomerID"].nunique())

# 5. Check negative and zero values
print("\nNon-positive values:")

for col in ["Recency", "Frequency", "Monetary", "AverageOrderValue"]:
    print(col, ":", (df_rfm[col] <= 0).sum())


# In[13]:


import matplotlib.pyplot as plt

features = [
    "Recency",
    "Frequency",
    "Monetary",
    "AverageOrderValue"
]

df_rfm[features].hist(
    bins=30,
    figsize=(12, 8)
)

plt.suptitle("Distribution of RFM Features")
plt.tight_layout()
plt.show()


# In[14]:


# Convert monetary variables to numeric types
df_rfm["Monetary"] = pd.to_numeric(df_rfm["Monetary"])

df_rfm["AverageOrderValue"] = pd.to_numeric(
    df_rfm["AverageOrderValue"]
)

# Select numerical clustering features
features = [
    "Recency",
    "Frequency",
    "Monetary",
    "AverageOrderValue"
]

df_cluster = df_rfm[features].copy()

# Check data types
print("Data types:")
display(df_cluster.dtypes)

# Check descriptive statistics
print("\nDescriptive statistics:")
display(df_cluster.describe())


# In[15]:


import matplotlib.pyplot as plt

df_cluster.hist(
    bins=30,
    figsize=(12, 8)
)

plt.suptitle("Distribution of Customer Clustering Features")
plt.tight_layout()
plt.show()


# In[16]:


print("Skewness:")
display(df_cluster.skew())


# In[17]:


for col in features:

    Q1 = df_cluster[col].quantile(0.25)
    Q3 = df_cluster[col].quantile(0.75)

    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = df_cluster[
        (df_cluster[col] < lower_bound) |
        (df_cluster[col] > upper_bound)
    ]

    print(f"\n{col}")
    print("Lower bound:", lower_bound)
    print("Upper bound:", upper_bound)
    print("Number of outliers:", len(outliers))


# In[18]:


import numpy as np
import matplotlib.pyplot as plt

# Apply Log Transformation
df_cluster_log = np.log1p(df_cluster)

# Check skewness after transformation
print("Skewness after Log Transformation:")
display(df_cluster_log.skew())

# Visualize distributions after transformation
df_cluster_log.hist(
    bins=30,
    figsize=(12, 8)
)

plt.suptitle("Distribution After Log Transformation")
plt.tight_layout()
plt.show()


# In[19]:


skewness_comparison = pd.DataFrame({
    "Before Log": df_cluster.skew(),
    "After Log": df_cluster_log.skew()
})

display(skewness_comparison)


# In[20]:


from sklearn.preprocessing import StandardScaler

# Initialize StandardScaler
scaler = StandardScaler()

# Standardize the transformed features
df_cluster_scaled = pd.DataFrame(
    scaler.fit_transform(df_cluster_log),
    columns=df_cluster_log.columns,
    index=df_cluster_log.index
)

# Check standardized data
print("Standardized data:")
display(df_cluster_scaled.head())

print("\nMean:")
display(df_cluster_scaled.mean())

print("\nStandard deviation:")
display(df_cluster_scaled.std())


# In[ ]:




