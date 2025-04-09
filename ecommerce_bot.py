import os
from dotenv import load_dotenv
sys.modules["sqlite3"] = pysqlite3
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai
import streamlit as st
from PIL import Image
import pandas as pd
from io import BytesIO
import requests

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define GeminiEmbeddingFunction
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.document_mode = True  # Specify if embedding documents or queries

    def __call__(self, input: Documents) -> Embeddings:
        task_type = "retrieval_document" if self.document_mode else "retrieval_query"
        response = genai.embed_content(
            model="models/text-embedding-004", content=input, task_type=task_type
        )
        return response["embedding"]

# Initialize ChromaDB
DB_NAME = "ecommerce_db"
embed_fn = GeminiEmbeddingFunction()
embed_fn.document_mode = True  # Start with document mode for embeddings
chroma_client = chromadb.PersistentClient(path="chroma_persistent_storage")
db = chroma_client.get_or_create_collection(name=DB_NAME, embedding_function=embed_fn)

# Streamlit UI
st.set_page_config(page_title="E-Commerce Chatbot", layout="wide")
st.title("E-Commerce Chatbot with Product Recommendations")
st.sidebar.header("Uploaded CSV Data")


def load_image(image_source, is_url=True):
    try:
        if is_url:
            response = requests.get(image_source)
            return Image.open(BytesIO(response.content))
        else:
            return Image.open(image_source)
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

# Assume CSV is already uploaded and embedded
uploaded_file = "temp.csv"  # Replace with dynamic path if needed

# Load CSV if uploaded
if uploaded_file:
    data = pd.read_csv(uploaded_file)
    st.sidebar.write("Data Preview:")
    st.sidebar.dataframe(data.head())

    # Embed documents if not already added
    if "documents_added" not in st.session_state:
        documents = [
            f"Product: {row['product_name']}, Rating: {row['rating']}, Price: {row['price']}, Image URL: {row['image_url']}"
            for _, row in data.iterrows()
        ]
        db.add(documents=documents, ids=[str(i) for i in range(len(documents))])
        st.session_state["documents_added"] = True
        st.sidebar.write("Documents have been embedded into ChromaDB.")

# Chatbot UI
st.header("Chat with the Bot")
user_query = st.text_input("Ask a question (e.g., 'Recommend affordable smartphones')", "")

if st.button("Submit Query"):
    if user_query:
        # Switch to query mode
        embed_fn.document_mode = False

        # Query ChromaDB
        result = db.query(query_texts=[user_query], n_results=3)
        relevant_passages = result["documents"]

        if relevant_passages:
            st.subheader("Recommended Products:")
            for idx, passage in enumerate(relevant_passages[0]):
                # Parse product details
                product_details = passage.split(", ")
                # product_info = {k: v for k, v in (detail.split(": ") for detail in product_details)}
                product_info = {}
                for detail in product_details:
                    try:
                        k, v = detail.split(": ", 1)  # Use maxsplit=1 to handle cases with multiple colons
                        product_info[k.strip()] = v.strip()
                    except ValueError:
                        # Log or handle unexpected strings gracefully
                        st.warning(f"Unexpected detail format: {detail}")

                # Display product details
                col1, col2 = st.columns([1, 2])
                # with col1:
                #     # Fetch and display the product image
                #     image_url = product_info.get("Image URL", "").strip()
                #     if image_url:
                #         response = requests.get(image_url)
                #         image = Image.open(BytesIO(response.content))
                #         st.image(image, use_container_width=True, caption=product_info.get("Product", "Product"))
                # with col2:
                #     st.write(f"**Name**: {product_info.get('Product', 'Unknown')}")
                #     st.write(f"**Rating**: {product_info.get('Rating', 'N/A')}")
                #     st.write(f"**Price**: {product_info.get('Price', 'N/A')}")

                with col1:
                    image_url = product_info.get("Image URL", "").strip()
                    img = load_image(image_url, is_url=True)
                    if img:
                        st.image(img, width=200)
                    else:
                        st.write("Image not available")
                with col2:
                    st.write(f"**Name**: {product_info.get('Product', 'Unknown')}")
                    st.write(f"**Rating**: {product_info.get('Rating', 'N/A')}")
                    st.write(f"**Price**: {product_info.get('Price', 'N/A')}")
                    # if st.button(f"Add {product['product_name']} to Cart", key=product["Unnamed: 0"]):
                    #     st.success(f"{product['product_name']} added to cart!")
                st.markdown("---")

            # Generate response using Gemini
            context = "\n\n".join(relevant_passages[0])
            prompt = (
                f"Use the following context to provide a concise response. If the answer is unclear, say 'I don't know.'"
                f"\n\nContext:\n{context}\n\nQuery:\n{user_query}"
            )
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            response = model.generate_content(prompt)
            st.subheader("AI Response:")
            st.write(response.text)
        else:
            st.write("No relevant products found.")
    else:
        st.write("Please enter a query.")
else:
    st.write("Enter a query to get recommendations.")

