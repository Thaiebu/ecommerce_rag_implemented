import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
import os
from vector_db_sematic_search import get_product_result



import logging

logging.basicConfig(level=logging.INFO)



# Configure the Streamlit page
st.set_page_config(
    page_title="E-commerce Store",
    page_icon="🛍️",
    layout="wide"
)

df = pd.read_csv('temp.csv')

# Load data from CSV
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('temp.csv')  # Replace with your CSV file path
        return df
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return pd.DataFrame()

def load_image(image_source, is_url=True):
    try:
        if is_url:
            response = requests.get(image_source)
            img = Image.open(BytesIO(response.content))
        else:
            img = Image.open(image_source)
        return img
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

# Initialize session state for chat
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def display_product_card(row):
    with st.container():
        col1, col2 = st.columns([1, 2])
        with col1:
            # Try loading from URL first, then from local path if URL fails
            img = None
            if pd.notna(row['image_url']):
                img = load_image(row['image_url'], is_url=True)
            if img is None and pd.notna(row['image_path']):
                img = load_image(row['image_path'], is_url=False)
            if img:
                st.image(img, width=200)
            else:
                st.write("Image not available")
        
        with col2:
            st.subheader(row['product_name'])
            st.write(f"Price: ${row['price']}")
            if pd.notna(row['rating']):
                st.write(f"Rating: {'⭐',row['rating']}")
            if st.button(f"Add to Cart 🛒", key=str(row.name)):
                st.success(f"{row['product_name']} added to cart!")

def chatbot_response(user_message):
    # Simple rule-based responses
    df = pd.read_csv('temp.csv')
    # responses = {
    #     "hello": "Hi! How can I help you today?",
    #     "help": "I can help you with:\n- Finding products\n- Checking prices\n- Product information",
    #     "prices": "Our prices range from $10 to $100. What's your budget?",
    #     "shipping": "We offer free shipping on orders over $50!",
    #     "return": "Our return policy allows returns within 30 days of purchase."
    # }
    
    # for key in responses:
    #     if key in user_message.lower():
    #         return responses[key]
    
    # Default to get_product_result if no match
    response = get_product_result(user_message, load_data())
    return str(response)

    
def main():
    # Load the data
    df = load_data()
    
    if df.empty:
        st.error("No product data available. Please check your CSV file.")
        return

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Products", "Shopping Cart", "Chat Support"])

    if page == "Products":
        st.title("Welcome to Our E-commerce Store 🛍️")
        
        # Search bar
        search_query = st.text_input("Search products...")
        
        # Filter products
        if search_query:
            filtered_df = df[df['product_name'].str.contains(search_query, case=False, na=False)]
        else:
            filtered_df = df

        # Add sorting options
        sort_option = st.selectbox(
            "Sort by:",
            ["Price (Low to High)", "Price (High to Low)", "Rating (High to Low)"]
        )

        if sort_option == "Price (Low to High)":
            filtered_df = filtered_df.sort_values('price')
        elif sort_option == "Price (High to Low)":
            filtered_df = filtered_df.sort_values('price', ascending=False)
        elif sort_option == "Rating (High to Low)":
            filtered_df = filtered_df.sort_values('rating', ascending=False)

        # Display products in a grid
        for idx, row in filtered_df.iterrows():
            display_product_card(row)
            st.markdown("---")

        if filtered_df.empty:
            st.info("No products found matching your search.")

    elif page == "Shopping Cart":
        st.title("Shopping Cart 🛒")
        st.info("Your cart is empty. Start shopping!")
        
        if st.button("Proceed to Checkout"):
            st.warning("Checkout functionality not implemented in this demo")

    elif page == "Chat Support":
        st.title("Customer Support Chat 💬")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        user_message = st.chat_input("Type your message here...")
        if user_message:
            # Display user message
            with st.chat_message("user"):
                st.write(user_message)
            st.session_state.chat_history.append({"role": "user", "content": user_message})
            
            # Display assistant response
            response = chatbot_response(user_message)
            with st.chat_message("assistant"):
                st.write(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()