import os
from groq import Groq

def get_grounded_answer(query, context):
    api_key = os.environ.get("GROQ_API_KEY", "")
    client = Groq(api_key=api_key if api_key else None)
    
    system_prompt = (
        "You are an expert AI assistant for AquaGuard AI, specializing in agriculture and water management.\n"
        "Follow these rules strictly:\n"
        "1. Answer using only the supplied document context.\n"
        "2. Do not invent facts that are not supported by the context.\n"
        "3. If the context does not contain enough information, say: \"I could not find enough information in the uploaded documents to answer that.\"\n"
        "4. Keep the answer clear and useful.\n"
        "5. When making factual claims, cite the supplied source labels in square brackets, for example [filename, p. X].\n"
        "6. Do not cite a source that does not support the claim."
    )
    
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error communicating with Groq API: {e}. Please ensure your GROQ_API_KEY environment variable is configured properly."