import uuid
import chromadb
import pandas as pd

df = pd.read_csv("temp.csv")



            
def sematic_search(search_query,df):
    client = chromadb.PersistentClient('vectorstore')
    collection = client.get_or_create_collection(name="ecom_phone")

    if not collection.count():
        for _, row in df.iterrows():
            collection.add(documents=row["product_name"],
                        metadatas={"image_url": row["image_url"]},
                        ids=[str(uuid.uuid4())])
    links = collection.query(query_texts=search_query, n_results=2).get('metadatas', [])
    return links[0]


# Function to get details based on the given image_url
def get_data_by_image_url(image_url,df):
    # Filter the DataFrame to find the row with the matching image_url
    result = df[df['image_url'] == image_url]
    if result.empty:
        return {"error": "No data found for the given image_url"}
    
    # Convert the result to JSON
    return result.to_dict(orient='records')


def get_product_result(search_query,df):
    links = sematic_search(search_query,df)
    result = []
    for link in links:
        res = get_data_by_image_url(link['image_url'],df)
        result.append(res)
    return result

if __name__ == "__main__":
    search_query = "Get Samsung phone details"
    print(get_product_result(search_query,df))



