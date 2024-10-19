import time
import os
import joblib
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import HTTPException
from typing import AsyncGenerator, Optional
import chromadb
from utils.llm_helpers import get_prompt
from pathlib import Path
from typing import Optional, Literal


class ChatAPI:
    def __init__(self):
        # Initialize ChromaDB and model
        self.db = chromadb.PersistentClient("db")
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        env_path = Path(".") / "chatbot_api" / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            # Fall back to loading .env from the current working directory
            load_dotenv()
        GOOGLE_API_KEY = os.environ.get("GENAI_KEY")
        if not GOOGLE_API_KEY:
            raise RuntimeError(
                "Google API key not found. Please set the GOOGLE_API_KEY environment variable."
            )

        # Configure Google Generative AI
        genai.configure(api_key=GOOGLE_API_KEY)

    # Function to query documents from ChromaDB
    def query_documents(
        self,
        query_texts,
        collection_name="astrolabe",
        n_results=2,
        where=None,
        where_document=None,
    ):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                collection = self.db.get_collection(name=collection_name)
                results = collection.query(
                    query_texts=query_texts,
                    n_results=n_results,
                    where=where,
                    where_document=where_document,
                )
                return results
            # except chromadb.ConnectionError:
            #     if attempt < max_retries - 1:
            #         time.sleep(2**attempt)
            #     else:
            #         raise HTTPException(
            #             status_code=500, detail="Database connection failed"
            #         )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    # Function to generate response from Generative AI
    async def generate_response(
        self,
        prompt: str,
        chat_id: Optional[str],
        object_name: str,
        age: str,
        level_of_interest: Literal["scholar", "wanderer", "muser"] = "muser",
        language: Literal["english", "german", "mandarin"] = "english",
    ) -> AsyncGenerator[str, None]:
        # Load past chats (if available)
        try:
            past_chats: dict = joblib.load("data/past_chats_list")
        except FileNotFoundError:
            past_chats = {}

        if chat_id not in past_chats:
            chat_id = str(time.time())
            past_chats[chat_id] = f"ChatSession-{chat_id}"
            joblib.dump(past_chats, "data/past_chats_list")

        # Load chat history
        try:
            gemini_history = joblib.load(f"data/{chat_id}-gemini_messages")
        except FileNotFoundError:
            gemini_history = []

        chat = self.model.start_chat(history=gemini_history)
        generation_config = genai.GenerationConfig(temperature=0.5)

        res = self.query_documents(prompt, object_name, n_results=2)
        if not res or not res["documents"]:
            raise HTTPException(status_code=404, detail="No relevant documents found")

        refined_prompt = get_prompt(
            language,
            prompt=prompt,
            doc1=res["documents"][0][0],
            doc2=res["documents"][0][1],
            age=age,
            level_of_interest=level_of_interest,
        )

        response_generator = chat.send_message(
            refined_prompt,
            stream=True,
            generation_config=generation_config,
        )
        return response_generator

    async def stream_response(self, response_generator) -> AsyncGenerator[str, None]:
        """Generator that streams response from AI in chunks."""
        try:
            for chunk in response_generator:
                if chunk.text:
                    yield chunk.text + " "
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


chat_instance = ChatAPI()
