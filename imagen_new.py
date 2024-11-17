import os
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from openai import OpenAI
from PIL import Image
import tempfile
from datetime import datetime

# Cargar las variables de entorno desde el archivo .env
load_dotenv()
openai_api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=openai_api_key)

# Rutas de archivos CSV
dataset_path = "imagenes/imagenes.csv"
new_dataset_path = "imagenes/nuevas_descripciones.csv"

# Cargar o inicializar los DataFrames
df = pd.read_csv(dataset_path, delimiter=';', encoding='ISO-8859-1')
if os.path.exists(new_dataset_path):
    new_df = pd.read_csv(new_dataset_path, delimiter=';', encoding='ISO-8859-1')
else:
    new_df = pd.DataFrame(columns=["imagen", "descripcion", "generated_description", "fecha"])

# Prompt para generar descripciones concisas
describe_system_prompt = '''
Eres un sistema especializado en generar descripciones breves y precisas para escenas culturales y eventos andinos, especialmente de la festividad de la Mamacha Carmen en Paucartambo. Describe de manera clara y objetiva la escena principal, destacando solo los elementos visibles y relevantes sin adornos adicionales. Mantente directo y conciso.
'''


def get_combined_examples(df):
    # Verificar que la columna 'generated_description' existe en el DataFrame
    if 'generated_description' not in df.columns:
        return "No hay descripciones generadas previas."

    # Generar un texto combinado de ejemplos a partir de descripciones previas
    combined_examples = "Ejemplos de descripciones previas:\n\n"
    for _, row in df.iterrows():
        if pd.notna(row.get('generated_description')) and pd.notna(row.get('descripcion')):
            combined_examples += f"Título: {row['descripcion']}\nDescripción: {row['generated_description']}\n\n"
    return combined_examples


def describe_image(img_url, title, example_descriptions):
    # Crear el prompt que incluye ejemplos previos como contexto
    prompt = f"{describe_system_prompt}\n\n{example_descriptions}\n\nGenera una descripción para la siguiente imagen:\nTítulo: {title}"

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": describe_system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


def generate_questions_from_description(description):
    # Genera preguntas dinámicas basadas en la descripción generada
    questions = [
        f"¿Qué elementos destacan en '{description[:50]}...'?",
        f"¿Cuál es el contexto cultural de esta escena?",
        "¿Qué simbolismo tiene esta imagen?"
    ]
    return questions


def export_to_csv(dataframe):
    # Exportar el historial como un archivo CSV descargable
    csv = dataframe.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar historial como CSV",
        data=csv,
        file_name="historial_descripciones.csv",
        mime="text/csv",
    )


# Inicializar la aplicación Streamlit
st.title("Generador de Descripciones de Imágenes de Danzas de Paucartambo")

# Sidebar para mostrar historial y opciones
with st.sidebar:
    st.write("Opciones")
    if st.checkbox("Mostrar historial"):
        st.dataframe(new_df[["imagen", "descripcion", "generated_description"]])
        export_to_csv(new_df)

# Opción para ingresar una URL de imagen o cargar un archivo de imagen
option = st.radio("Seleccione el método para proporcionar una imagen:", ("URL de imagen", "Subir imagen"))

if option == "URL de imagen":
    img_url = st.text_input("Ingrese la URL de la imagen")
    title = st.text_input("Ingrese un título o descripción breve de la imagen")
    if img_url and title:
        st.image(img_url, caption="Imagen desde URL", use_column_width=True)
        example_descriptions = get_combined_examples(new_df)
        if st.button("Generar Descripción"):
            try:
                description = describe_image(img_url, title, example_descriptions)
                st.write("Descripción en español:")
                st.write(description)

                # Guardar la nueva descripción en el DataFrame y en el archivo CSV
                new_row = {
                    "imagen": img_url,
                    "descripcion": title,
                    "generated_description": description,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                new_df = pd.concat([new_df, pd.DataFrame([new_row])], ignore_index=True)
                new_df.to_csv(new_dataset_path, sep=';', index=False, encoding='ISO-8859-1')

                # Generar preguntas dinámicas basadas en la descripción
                dynamic_questions = generate_questions_from_description(description)
                st.write("**Preguntas relacionadas:**")
                for q in dynamic_questions:
                    if st.button(q):
                        st.write(f"Respuesta a: {q}")  # Placeholder
            except Exception as e:
                st.error(f"Error al generar la descripción: {e}")
else:
    uploaded_file = st.file_uploader("Cargue una imagen", type=["jpg", "jpeg", "png"])
    title = st.text_input("Ingrese un título o descripción breve de la imagen")

    if uploaded_file and title:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen cargada", use_column_width=True)

        # Guardar temporalmente la imagen y generar una URL temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            img_url = temp_file.name

        example_descriptions = get_combined_examples(new_df)
        if st.button("Generar Descripción"):
            try:
                description = describe_image(img_url, title, example_descriptions)
                st.write("Descripción en español:")
                st.write(description)

                # Guardar la nueva descripción en el DataFrame y en el archivo CSV
                new_row = {
                    "imagen": img_url,
                    "descripcion": title,
                    "generated_description": description,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                new_df = pd.concat([new_df, pd.DataFrame([new_row])], ignore_index=True)
                new_df.to_csv(new_dataset_path, sep=';', index=False, encoding='ISO-8859-1')

                # Generar preguntas dinámicas basadas en la descripción
                dynamic_questions = generate_questions_from_description(description)
                st.write("**Preguntas relacionadas:**")
                for q in dynamic_questions:
                    if st.button(q):
                        st.write(f"Respuesta a: {q}")  # Placeholder
            except Exception as e:
                st.error(f"Error al generar la descripción: {e}")
