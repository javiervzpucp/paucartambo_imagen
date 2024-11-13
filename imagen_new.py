import os
import streamlit as st
import pandas as pd
import openai
from PIL import Image

# Cargar las variables de entorno desde el archivo .env
#load_dotenv()
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Rutas de archivos CSV
dataset_path = "imagenes/imagenes.csv"
new_dataset_path = "imagenes/nuevas_descripciones.csv"

# Cargar o inicializar los DataFrames
df = pd.read_csv(dataset_path, delimiter=';',encoding='latin-1')
if os.path.exists(new_dataset_path):
    new_df = pd.read_csv(new_dataset_path, delimiter=';',encoding='latin-1')
else:
    new_df = pd.DataFrame(columns=["imagen", "descripcion", "generated_description"])

# Prompt para generar descripciones concisas
describe_system_prompt = '''
Eres un sistema especializado en generar descripciones breves y precisas para escenas culturales y eventos andinos, especialmente de la festividad de la Mamacha Carmen en Paucartambo. Describe de manera clara y objetiva la escena principal, destacando solo los elementos visibles y relevantes sin adornos adicionales. Mantente directo y conciso.
'''

def get_combined_examples(df):
    # Generar un texto combinado de ejemplos a partir de descripciones previas
    combined_examples = "Ejemplos de descripciones previas:\n\n"
    for _, row in df.iterrows():
        if pd.notna(row['generated_description']):
            combined_examples += f"Título: {row['descripcion']}\nDescripción: {row['generated_description']}\n\n"
    return combined_examples

def describe_image(img_url, title, example_descriptions):
    # Crear el prompt que incluye ejemplos previos como contexto
    prompt = f"{describe_system_prompt}\n\n{example_descriptions}\n\nGenera una descripción para la siguiente imagen:\nTítulo: {title}"

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": describe_system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.1
    )
    return response.choices[0].message.content.strip()

# Función para almacenar descripciones en el nuevo CSV
def generate_and_store_descriptions(df, new_df):
    # Crear el texto combinado de ejemplos una vez, para usar en cada nueva descripción
    example_descriptions = get_combined_examples(df)

    for index, row in df.iterrows():
        img_url = row['imagen']
        title = row['descripcion']
        description = describe_image(img_url, title, example_descriptions)
        new_df = new_df._append({"imagen": img_url, "descripcion": title, "generated_description": description}, ignore_index=True)

    new_df.to_csv(new_dataset_path, sep=';', index=False)
    print(f"Descripciones generadas y guardadas en el archivo {new_dataset_path}.")

# Inicializar la aplicación Streamlit
st.title("Generador de Descripciones de Imágenes de las Devociones Marianas de Paucartambo")

# Opción para ingresar una URL de imagen o cargar un archivo de imagen
option = st.radio("Seleccione el método para proporcionar una imagen:", ("URL de imagen", "Subir imagen"))

if option == "URL de imagen":
    img_url = st.text_input("Ingrese la URL de la imagen")
    title = st.text_input("Ingrese un título o descripción breve de la imagen")
    if img_url and title:
        # Mostrar la imagen
        st.image(img_url, caption="Imagen desde URL", use_column_width=True)
        
        # Obtener ejemplos combinados de descripciones previas
        example_descriptions = get_combined_examples(new_df)
        
        # Generar descripción
        if st.button("Generar Descripción"):
            description = describe_image(img_url, title, example_descriptions)
            st.write("Descripción generada:")
            st.write(description)
            
            # Guardar la nueva descripción en el DataFrame y en el archivo CSV
            new_df = new_df._append({"imagen": img_url, "descripcion": title, "generated_description": description}, ignore_index=True)
            new_df.to_csv(new_dataset_path, sep=';', index=False)

else:
    uploaded_file = st.file_uploader("Cargue una imagen", type=["jpg", "jpeg", "png"])
    title = st.text_input("Ingrese un título o descripción breve de la imagen")
    
    if uploaded_file and title:
        # Mostrar la imagen
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen cargada", use_column_width=True)
        
        # Guardar temporalmente la imagen y generar una URL temporal
        img_url = f"imagen_cargada_{uploaded_file.name}"
        
        # Obtener ejemplos combinados de descripciones previas
        example_descriptions = get_combined_examples(new_df)
        
        # Generar descripción
        if st.button("Generar Descripción"):
            description = describe_image(img_url, title, example_descriptions)
            st.write("Descripción generada:")
            st.write(description)
            
            # Guardar la nueva descripción en el DataFrame y en el archivo CSV
            new_df = new_df._append({"imagen": img_url, "descripcion": title, "generated_description": description}, ignore_index=True)
            new_df.to_csv(new_dataset_path, sep=';', index=False)

# Mostrar el historial de descripciones generadas
st.write("Historial de descripciones generadas:")
st.dataframe(new_df[["imagen", "descripcion", "generated_description"]])
