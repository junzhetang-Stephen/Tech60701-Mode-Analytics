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


# In[21]:


from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

inertia = []
silhouette_scores = []
K_range = range(2, 11)

for k in K_range:

    kmeans = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    labels = kmeans.fit_predict(df_cluster_scaled)

    inertia.append(kmeans.inertia_)

    silhouette_scores.append(
        silhouette_score(df_cluster_scaled, labels)
    )

# Elbow Method
plt.figure(figsize=(8, 5))
plt.plot(K_range, inertia, marker="o")
plt.xlabel("Number of Clusters (K)")
plt.ylabel("Inertia")
plt.title("Elbow Method")
plt.xticks(K_range)
plt.show()

# Silhouette Score
plt.figure(figsize=(8, 5))
plt.plot(K_range, silhouette_scores, marker="o")
plt.xlabel("Number of Clusters (K)")
plt.ylabel("Silhouette Score")
plt.title("Silhouette Score")
plt.xticks(K_range)
plt.show()

# Display results
results = pd.DataFrame({
    "K": list(K_range),
    "Inertia": inertia,
    "Silhouette Score": silhouette_scores
})

display(results)


# In[22]:


from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

k_values = [2, 4, 8]

comparison = []

for k in k_values:

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    labels = model.fit_predict(df_cluster_scaled)

    score = silhouette_score(
        df_cluster_scaled,
        labels
    )

    sizes = pd.Series(labels).value_counts().sort_index()

    comparison.append({
        "K": k,
        "Silhouette Score": score,
        "Cluster Sizes": sizes.to_dict()
    })

display(pd.DataFrame(comparison))


# In[23]:


from sklearn.cluster import KMeans

k_values = [2, 4, 8]

cluster_profiles = {}

for k in k_values:

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    labels = model.fit_predict(df_cluster_scaled)

    # Combine original features with cluster labels
    df_result = df_cluster.copy()
    df_result["Cluster"] = labels

    # Calculate cluster sizes
    cluster_sizes = df_result["Cluster"].value_counts().sort_index()

    # Calculate average customer characteristics
    profile = df_result.groupby("Cluster")[features].mean()

    # Add number of customers
    profile.insert(0, "NumberOfCustomers", cluster_sizes)

    cluster_profiles[k] = profile

    print(f"\n========== K = {k} ==========")
    display(profile.round(2))


# In[24]:


# Calculate feature correlations
correlation_matrix = df_cluster_log.corr()

print("Feature Correlation Matrix:")
display(correlation_matrix.round(3))

# Visualize correlation matrix
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 6))

sns.heatmap(
    correlation_matrix,
    annot=True,
    cmap="coolwarm",
    fmt=".2f"
)

plt.title("Feature Correlation Matrix")
plt.show()


# In[25]:


from sklearn.preprocessing import StandardScaler

# Select three RFM features
features_rfm = [
    "Recency",
    "Frequency",
    "Monetary"
]

# Remove AverageOrderValue
df_rfm_selected = df_cluster_log[features_rfm].copy()

# Standardize the selected features
scaler_rfm = StandardScaler()

df_rfm_scaled = pd.DataFrame(
    scaler_rfm.fit_transform(df_rfm_selected),
    columns=features_rfm,
    index=df_rfm_selected.index
)

# Check results
print("Mean:")
display(df_rfm_scaled.mean())

print("Standard deviation:")
display(df_rfm_scaled.std())


# In[27]:


from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

inertia_rfm = []
silhouette_rfm = []

K_range = range(2, 11)

for k in K_range:

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    labels = model.fit_predict(df_rfm_scaled)

    inertia_rfm.append(model.inertia_)

    silhouette_rfm.append(
        silhouette_score(df_rfm_scaled, labels)
    )

# Display results
results_rfm = pd.DataFrame({
    "K": list(K_range),
    "Inertia": inertia_rfm,
    "Silhouette Score": silhouette_rfm
})

display(results_rfm)


# In[28]:


from sklearn.cluster import KMeans
import pandas as pd

# Train the final K-Means model
final_kmeans = KMeans(
    n_clusters=10,
    random_state=42,
    n_init=10
)

# Assign cluster labels
cluster_labels = final_kmeans.fit_predict(df_rfm_scaled)

# Add cluster labels to the original RFM dataset
df_final = df_rfm.loc[df_rfm_scaled.index].copy()
df_final["Cluster"] = cluster_labels

# Display the first rows
display(df_final.head())

# Display cluster sizes
print("Number of customers in each cluster:")
display(
    df_final["Cluster"]
    .value_counts()
    .sort_index()
)


# In[29]:


# Calculate customer profiles using original values
cluster_profile = df_final.groupby("Cluster").agg(
    NumberOfCustomers=("CustomerID", "count"),
    AvgRecency=("Recency", "mean"),
    AvgFrequency=("Frequency", "mean"),
    AvgMonetary=("Monetary", "mean")
).round(2)

display(cluster_profile)


# In[30]:


import matplotlib.pyplot as plt

cluster_sizes = df_final["Cluster"].value_counts().sort_index()

plt.figure(figsize=(9, 5))

cluster_sizes.plot(kind="bar")

plt.xlabel("Cluster")
plt.ylabel("Number of Customers")
plt.title("Customer Distribution Across 10 Clusters")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()


# In[31]:


from sklearn.metrics import silhouette_score

final_score = silhouette_score(
    df_rfm_scaled,
    cluster_labels
)

print("Final K-Means Silhouette Score:", round(final_score, 4))


# Résultats de la segmentation des clients avec K-Means
# - 19 119 clients répartis en 10 clusters.
# - Score Silhouette final : 0,4441.
# - Identification de différents profils de consommation.
# - Le cluster 4 représente les clients VIP, avec une dépense moyenne particulièrement élevée.
# - Le cluster 9 regroupe des clients à forte valeur et à fréquence d'achat élevée.
# - Le cluster 1 représente le groupe le plus nombreux, caractérisé par une faible fréquence d'achat et une faible dépense moyenne.
# Conclusion :
# La méthode K-Means permet d'identifier dix segments de clients ayant des comportements d'achat différents, ce qui peut aider à adapter les stratégies marketing à chaque groupe.

# In[32]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

sns.set_theme(style="whitegrid", context="notebook")

# Reconstruct the dataset safely
plot_data = df_final[
    ["Recency", "Frequency", "Monetary", "Cluster"]
].copy()

# ==========================================
# 1. PCA CLUSTER VISUALIZATION
# ==========================================

pca = PCA(n_components=2)

pca_results = pca.fit_transform(df_rfm_scaled)

pca_df = pd.DataFrame(
    pca_results,
    columns=["PC1", "PC2"],
    index=df_rfm_scaled.index
)

pca_df["Cluster"] = cluster_labels.astype(str)

plt.figure(figsize=(12, 8))

sns.scatterplot(
    data=pca_df,
    x="PC1",
    y="PC2",
    hue="Cluster",
    palette="tab10",
    s=18,
    alpha=0.55,
    linewidth=0
)

plt.title(
    "Customer Segmentation - PCA Visualization",
    fontsize=17,
    fontweight="bold"
)

plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")

plt.legend(
    title="Cluster",
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()
plt.show()

print(
    "Explained variance:",
    round(pca.explained_variance_ratio_.sum() * 100, 2),
    "%"
)


# ==========================================
# 2. RFM CLUSTER HEATMAP
# ==========================================

profile = plot_data.groupby("Cluster")[
    ["Recency", "Frequency", "Monetary"]
].mean()

# Standardize the cluster averages for comparison
profile_z = (
    profile - profile.mean()
) / profile.std()

plt.figure(figsize=(11, 7))

sns.heatmap(
    profile_z,
    annot=True,
    fmt=".2f",
    cmap="RdYlBu_r",
    center=0,
    linewidths=0.8,
    cbar_kws={"label": "Standardized Cluster Mean"}
)

plt.title(
    "RFM Customer Profile Heatmap",
    fontsize=17,
    fontweight="bold"
)

plt.xlabel("RFM Features")
plt.ylabel("Customer Cluster")

plt.tight_layout()
plt.show()


# ==========================================
# 3. CUSTOMER VALUE BUBBLE CHART
# ==========================================

bubble_data = plot_data.groupby("Cluster").agg(
    Recency=("Recency", "mean"),
    Frequency=("Frequency", "mean"),
    Monetary=("Monetary", "mean"),
    Customers=("Cluster", "size")
).reset_index()

plt.figure(figsize=(12, 8))

scatter = plt.scatter(
    bubble_data["Recency"],
    np.log1p(bubble_data["Monetary"]),
    s=bubble_data["Customers"] * 0.10,
    c=bubble_data["Frequency"],
    cmap="viridis",
    alpha=0.8,
    edgecolors="black",
    linewidths=0.8
)

for _, row in bubble_data.iterrows():
    plt.annotate(
        f"C{int(row['Cluster'])}",
        (row["Recency"], np.log1p(row["Monetary"])),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=10,
        fontweight="bold"
    )

plt.colorbar(scatter, label="Average Purchase Frequency")

plt.title(
    "Customer Value Segmentation",
    fontsize=17,
    fontweight="bold"
)

plt.xlabel("Average Recency (Days)")
plt.ylabel("Log Average Monetary Value")

plt.tight_layout()
plt.show()


# ==========================================
# 4. RFM RADAR CHART
# ==========================================

from math import pi

radar_features = ["Recency", "Frequency", "Monetary"]

# Normalize the cluster profiles to 0-1
radar_data = profile.copy()

radar_data = (
    radar_data - radar_data.min()
) / (
    radar_data.max() - radar_data.min()
)

categories = radar_features
N = len(categories)

angles = [
    n / float(N) * 2 * pi
    for n in range(N)
]

angles += angles[:1]

fig, ax = plt.subplots(
    figsize=(10, 10),
    subplot_kw={"polar": True}
)

colors = plt.cm.tab10(np.linspace(0, 1, 10))

for i, cluster in enumerate(radar_data.index):

    values = radar_data.loc[cluster].tolist()
    values += values[:1]

    ax.plot(
        angles,
        values,
        linewidth=1.8,
        label=f"Cluster {cluster}",
        color=colors[i]
    )

    ax.fill(
        angles,
        values,
        alpha=0.04,
        color=colors[i]
    )

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12)

ax.set_title(
    "RFM Profiles Across Customer Clusters",
    fontsize=16,
    fontweight="bold",
    pad=25
)

ax.legend(
    loc="upper right",
    bbox_to_anchor=(1.35, 1.15),
    title="Customer Groups"
)

plt.tight_layout()
plt.show()


# In[33]:


from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Reduce dimensions to 2D
pca = PCA(n_components=2)
X_pca = pca.fit_transform(df_rfm_scaled)

pca_df = pd.DataFrame(
    X_pca,
    columns=["PC1", "PC2"]
)

pca_df["Cluster"] = cluster_labels

plt.figure(figsize=(13, 9))

sns.scatterplot(
    data=pca_df,
    x="PC1",
    y="PC2",
    hue="Cluster",
    palette="tab10",
    s=22,
    alpha=0.65
)

plt.title("K-Means Customer Clustering (K=10)", fontsize=18)
plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.legend(title="Cluster", bbox_to_anchor=(1.02, 1))
plt.tight_layout()
plt.show()

print(
    "Explained variance:",
    round(pca.explained_variance_ratio_.sum() * 100, 2),
    "%"
)


# In[34]:


from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure(figsize=(13, 10))
ax = fig.add_subplot(111, projection="3d")

scatter = ax.scatter(
    df_rfm_scaled["Recency"],
    df_rfm_scaled["Frequency"],
    df_rfm_scaled["Monetary"],
    c=cluster_labels,
    cmap="tab10",
    s=12,
    alpha=0.6
)

ax.set_title("3D K-Means Customer Segmentation (K=10)", pad=20)
ax.set_xlabel("Recency")
ax.set_ylabel("Frequency")
ax.set_zlabel("Monetary")

plt.colorbar(scatter, ax=ax, label="Cluster", shrink=0.65)
plt.show()


# In[35]:


import numpy as np

centers = pd.DataFrame(
    final_kmeans.cluster_centers_,
    columns=["Recency", "Frequency", "Monetary"]
)

plt.figure(figsize=(12, 7))

sns.heatmap(
    centers,
    annot=True,
    fmt=".2f",
    cmap="RdYlBu_r",
    center=0,
    linewidths=0.5
)

plt.title("K-Means Cluster Centroids (K=10)", fontsize=17)
plt.xlabel("RFM Features")
plt.ylabel("Cluster")

plt.tight_layout()
plt.show()


# In[36]:


df_rfm_scaled


# In[37]:


import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram

# Random sampling for dendrogram
np.random.seed(42)

sample_indices = np.random.choice(
    len(df_rfm_scaled),
    size=1500,
    replace=False
)

X_sample = df_rfm_scaled.iloc[sample_indices]

# Ward linkage
Z = linkage(X_sample, method='ward')

# Plot dendrogram
plt.figure(figsize=(16, 7))

dendrogram(
    Z,
    truncate_mode='lastp',
    p=30,
    leaf_rotation=90,
    leaf_font_size=10
)

plt.title("Hierarchical Clustering Dendrogram (Ward Method)")
plt.xlabel("Customer Groups")
plt.ylabel("Euclidean Distance")
plt.tight_layout()
plt.show()


# In[38]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# SQL query: monthly product sales
query = """
SELECT
    DATEFROMPARTS(
        YEAR(h.OrderDate),
        MONTH(h.OrderDate),
        1
    ) AS OrderMonth,
    d.ProductID,
    p.ProductSubcategoryID,
    SUM(d.OrderQty) AS MonthlyQty,
    SUM(d.LineTotal) AS MonthlyRevenue,
    AVG(d.UnitPrice) AS AvgUnitPrice,
    COUNT(DISTINCT h.SalesOrderID) AS OrderCount

FROM Sales.SalesOrderHeader h

INNER JOIN Sales.SalesOrderDetail d
    ON h.SalesOrderID = d.SalesOrderID

INNER JOIN Production.Product p
    ON d.ProductID = p.ProductID

GROUP BY
    YEAR(h.OrderDate),
    MONTH(h.OrderDate),
    d.ProductID,
    p.ProductSubcategoryID

ORDER BY
    OrderMonth,
    d.ProductID;
"""

# Execute query
cursor.execute(query)

columns = [column[0] for column in cursor.description]
df_sales_monthly = pd.DataFrame.from_records(
    cursor.fetchall(),
    columns=columns
)

df_sales_monthly["OrderMonth"] = pd.to_datetime(
    df_sales_monthly["OrderMonth"]
)

print("Dataset shape:", df_sales_monthly.shape)
print("\nFirst rows:")
display(df_sales_monthly.head())

print("\nDate range:")
print(df_sales_monthly["OrderMonth"].min())
print(df_sales_monthly["OrderMonth"].max())

print("\nNumber of products:",
      df_sales_monthly["ProductID"].nunique())

print("\nNumber of months:",
      df_sales_monthly["OrderMonth"].nunique())


# In[39]:


# Monthly total sales quantity
df_monthly_total = (
    df_sales_monthly
    .groupby("OrderMonth")["MonthlyQty"]
    .sum()
    .reset_index()
)

plt.figure(figsize=(14, 5))

plt.plot(
    df_monthly_total["OrderMonth"],
    df_monthly_total["MonthlyQty"],
    marker="o"
)

plt.title("Monthly Sales Quantity - AdventureWorks2025")
plt.xlabel("Month")
plt.ylabel("Total Sales Quantity")
plt.xticks(rotation=45)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

display(df_monthly_total.head())


# In[40]:


# 1. Create complete monthly date range
all_months = pd.date_range(
    start=df_sales_monthly["OrderMonth"].min(),
    end=df_sales_monthly["OrderMonth"].max(),
    freq="MS"
)

all_products = sorted(df_sales_monthly["ProductID"].unique())

# 2. Create product-month quantity matrix
sales_matrix = (
    df_sales_monthly
    .pivot_table(
        index="OrderMonth",
        columns="ProductID",
        values="MonthlyQty",
        aggfunc="sum"
    )
    .reindex(index=all_months, columns=all_products)
    .fillna(0)
)

print("Sales matrix shape:", sales_matrix.shape)
print("\nMonthly sales quantity:")
display(sales_matrix.head())

# 3. Check zero values
zero_ratio = (sales_matrix == 0).sum().sum() / sales_matrix.size

print("Number of products:", sales_matrix.shape[1])
print("Number of months:", sales_matrix.shape[0])
print("Zero sales ratio:", round(zero_ratio * 100, 2), "%")

# 4. Plot selected products
plt.figure(figsize=(14, 6))

for product_id in all_products[:5]:
    plt.plot(
        sales_matrix.index,
        sales_matrix[product_id],
        label=f"Product {product_id}"
    )

plt.title("Monthly Sales Quantity - Selected Products")
plt.xlabel("Month")
plt.ylabel("Sales Quantity")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()


# In[41]:


query_check = """
SELECT
    MIN(OrderDate) AS FirstOrderDate,
    MAX(OrderDate) AS LastOrderDate,
    COUNT(*) AS TotalOrders
FROM Sales.SalesOrderHeader;
"""

cursor.execute(query_check)
row = cursor.fetchone()

print("First order date:", row[0])
print("Last order date:", row[1])
print("Total orders:", row[2])


# In[42]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Parameters
LOOKBACK = 12

# Build sequences for all products
X_list = []
y_list = []
target_months = []

for product_id in sales_matrix.columns:

    values = sales_matrix[product_id].values.astype(float)

    # Log transformation
    values = np.log1p(values)

    for i in range(LOOKBACK, len(values)):

        X_list.append(values[i-LOOKBACK:i])
        y_list.append(values[i])
        target_months.append(i)

X_all = np.array(X_list).reshape(-1, LOOKBACK, 1)
y_all = np.array(y_list).reshape(-1, 1)
target_months = np.array(target_months)

# Chronological split
train_mask = target_months < 30
valid_mask = (target_months >= 30) & (target_months < 34)
test_mask = target_months >= 34

X_train = X_all[train_mask]
X_valid = X_all[valid_mask]
X_test = X_all[test_mask]

y_train = y_all[train_mask]
y_valid = y_all[valid_mask]
y_test = y_all[test_mask]

print("X_train:", X_train.shape)
print("X_valid:", X_valid.shape)
print("X_test:", X_test.shape)

print("y_train:", y_train.shape)
print("y_valid:", y_valid.shape)
print("y_test:", y_test.shape)


# In[43]:


# Fit scalers only on training data
scaler_X = StandardScaler()
scaler_y = StandardScaler()

X_train_scaled = scaler_X.fit_transform(
    X_train.reshape(-1, 1)
).reshape(X_train.shape)

X_valid_scaled = scaler_X.transform(
    X_valid.reshape(-1, 1)
).reshape(X_valid.shape)

X_test_scaled = scaler_X.transform(
    X_test.reshape(-1, 1)
).reshape(X_test.shape)

y_train_scaled = scaler_y.fit_transform(y_train)
y_valid_scaled = scaler_y.transform(y_valid)
y_test_scaled = scaler_y.transform(y_test)

print("Preprocessing completed.")


# In[44]:


import tensorflow as tf

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

tf.keras.utils.set_random_seed(42)

# Build GRU model
gru_model = Sequential([
    tf.keras.Input(shape=(LOOKBACK, 1)),

    GRU(64, return_sequences=True),
    Dropout(0.2),

    GRU(32),
    Dropout(0.2),

    Dense(16, activation="relu"),
    Dense(1)
])

gru_model.compile(
    optimizer="adam",
    loss="mse",
    metrics=["mae"]
)

gru_model.summary()

# Callbacks
early_stop = EarlyStopping(
    monitor="val_loss",
    patience=15,
    restore_best_weights=True
)

reduce_lr = ReduceLROnPlateau(
    monitor="val_loss",
    factor=0.5,
    patience=5,
    min_lr=0.00001
)

# Train
history_gru = gru_model.fit(
    X_train_scaled,
    y_train_scaled,
    validation_data=(X_valid_scaled, y_valid_scaled),
    epochs=100,
    batch_size=64,
    callbacks=[early_stop, reduce_lr],
    verbose=1
)


# In[46]:


import tensorflow as tf

from tensorflow.keras.layers import (
    Input, Dense, Dropout,
    MultiHeadAttention,
    LayerNormalization,
    GlobalAveragePooling1D,
    Add, Embedding
)
from tensorflow.keras.models import Model

def build_transformer():

    inputs = Input(shape=(LOOKBACK, 1))

    # Project input features
    x = Dense(32)(inputs)

    # Positional embedding
    positions = tf.range(0, LOOKBACK)
    position_embedding = Embedding(
        input_dim=LOOKBACK,
        output_dim=32
    )(positions)

    x = x + position_embedding

    # Self-attention
    attention = MultiHeadAttention(
        num_heads=4,
        key_dim=8
    )(x, x)

    x = Add()([x, attention])
    x = LayerNormalization()(x)

    # Feed-forward network
    ff = Dense(64, activation="relu")(x)
    ff = Dropout(0.2)(ff)
    ff = Dense(32)(ff)

    x = Add()([x, ff])
    x = LayerNormalization()(x)

    # One prediction per sequence
    x = GlobalAveragePooling1D()(x)
    x = Dense(32, activation="relu")(x)
    x = Dropout(0.2)(x)

    outputs = Dense(1)(x)

    model = Model(inputs=inputs, outputs=outputs)

    model.compile(
        optimizer="adam",
        loss="mse",
        metrics=["mae"]
    )

    return model


transformer_model = build_transformer()

transformer_model.summary()

print("Output shape:", transformer_model.output_shape)


# In[47]:


history_transformer = transformer_model.fit(
    X_train_scaled,
    y_train_scaled,
    validation_data=(
        X_valid_scaled,
        y_valid_scaled
    ),
    epochs=100,
    batch_size=64,
    callbacks=[early_stop, reduce_lr],
    verbose=1
)


# In[48]:


plt.figure(figsize=(10, 5))

plt.plot(
    history_transformer.history["loss"],
    label="Training Loss"
)

plt.plot(
    history_transformer.history["val_loss"],
    label="Validation Loss"
)

plt.title("Transformer Training and Validation Loss")
plt.xlabel("Epoch")
plt.ylabel("MSE Loss")
plt.legend()
plt.grid(alpha=0.3)
plt.show()


# In[49]:


print("Target scaler:", scaler_y)


# In[50]:


import numpy as np
import pandas as pd

# Transformer predictions
y_pred_scaled = transformer_model.predict(X_valid_scaled)

# Inverse transformation
y_pred = scaler_y.inverse_transform(
    y_pred_scaled.reshape(-1, 1)
).flatten()

y_actual = scaler_y.inverse_transform(
    np.array(y_valid_scaled).reshape(-1, 1)
).flatten()

# Sales quantity cannot be negative
y_pred = np.maximum(y_pred, 0)

print("Actual sales:", y_actual[:10])
print("Predicted sales:", y_pred[:10])


# In[51]:


from sklearn.metrics import mean_absolute_error, mean_squared_error

mae = mean_absolute_error(y_actual, y_pred)

rmse = np.sqrt(
    mean_squared_error(y_actual, y_pred)
)

wape = (
    np.sum(np.abs(y_actual - y_pred))
    / np.sum(np.abs(y_actual))
) * 100

print("========== Transformer Evaluation ==========")
print(f"MAE  : {mae:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"WAPE : {wape:.2f}%")


# In[52]:


import matplotlib.pyplot as plt

plt.figure(figsize=(14, 6))

plt.plot(
    y_actual[:200],
    label="Actual Sales",
    marker="o",
    markersize=3
)

plt.plot(
    y_pred[:200],
    label="Predicted Sales",
    marker="x",
    markersize=3
)

plt.title("Transformer: Actual vs Predicted Sales")
plt.xlabel("Validation Samples")
plt.ylabel("Monthly Sales Quantity")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()


# In[54]:


import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 1. Inverse StandardScaler
y_pred_log = scaler_y.inverse_transform(
    transformer_model.predict(X_valid_scaled)
).flatten()

y_actual_log = scaler_y.inverse_transform(
    np.array(y_valid_scaled).reshape(-1, 1)
).flatten()

# 2. Inverse log1p transformation
y_pred_original = np.expm1(y_pred_log)
y_actual_original = np.expm1(y_actual_log)

# Avoid negative predictions
y_pred_original = np.maximum(y_pred_original, 0)

# 3. Calculate metrics in original sales scale
mae_original = mean_absolute_error(
    y_actual_original, y_pred_original
)

rmse_original = np.sqrt(
    mean_squared_error(y_actual_original, y_pred_original)
)

wape_original = (
    np.sum(np.abs(y_actual_original - y_pred_original))
    / np.sum(np.abs(y_actual_original))
) * 100

print("===== Transformer: Original Sales Scale =====")
print(f"MAE  : {mae_original:.2f}")
print(f"RMSE : {rmse_original:.2f}")
print(f"WAPE : {wape_original:.2f}%")

print("\nActual sales:", y_actual_original[:10])
print("Predicted sales:", y_pred_original[:10])


# In[55]:


import matplotlib.pyplot as plt

plt.figure(figsize=(14, 6))

plt.plot(
    y_actual_original[:200],
    label="Actual Sales",
    marker="o",
    markersize=3
)

plt.plot(
    y_pred_original[:200],
    label="Predicted Sales",
    marker="x",
    markersize=3
)

plt.title("Transformer: Actual vs Predicted Sales")
plt.xlabel("Validation Samples")
plt.ylabel("Monthly Sales Quantity")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()


# In[ ]:




