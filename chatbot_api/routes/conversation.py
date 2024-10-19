from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from chat_api import chat_instance

router = APIRouter(
    prefix="/api",
    tags=["Detect Object in Image"],
)


@router.post("/chat")
async def chat(request: Request):
    data = await request.json()
    prompt = data.get("prompt")
    chat_id = data.get("chat_id")
    object_name = data.get("object_name")
    language = data.get("language") or "english"
    age = str(data.get("age"))
    level_of_interest = data.get("level_of_interest")
    response_generator = await chat_instance.generate_response(
        prompt, chat_id, object_name, age, level_of_interest, language
    )

    # Stream response back to client
    return StreamingResponse(
        chat_instance.stream_response(response_generator), media_type="text/plain"
    )
