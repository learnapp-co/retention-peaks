import os
from dotenv import load_dotenv
import pinecone
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pprint import pprint
from langchain_openai import ChatOpenAI
from langchain.chains.retrieval_qa.base import RetrievalQA
import sys

sys.path.append("/Users/nostradamus/personal/Yotube-Search-Bot/Confucius")
from src.services.init_services import init_services
from src.models.workspace import Video


# Load environment variables
load_dotenv()

# Initialize Pinecone
pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or "OPENAI_API_KEY"

model_name = "text-embedding-ada-002"

# Initialize OpenAI embeddings
embed = OpenAIEmbeddings(model=model_name, openai_api_key=OPENAI_API_KEY)


def setup_test_index(index_name="confucius-test"):
    """Create a test index if it doesn't exist"""
    existing_indexes = [
        index.name for index in pc.list_indexes()
    ]  # Convert to list of strings
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            metric="cosine",
            dimension=1536,
            spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    else:
        print(f"Index '{index_name}' already exists. Using existing index.")
    return pc.Index(index_name)


async def test_basic_operations():
    """Test basic vector operations"""
    index_name = "videos-index"
    await init_services()

    videosData = await Video.find(
        {"video_id": {"$in": ["-0hSJqsc2g8", "-1DeU6t38aM"]}}
    ).to_list()

    if not videosData:
        print("No videos found")
        return

    # Prepare vectors with proper data access
    vectors = []
    for video in videosData:
        try:
            # Convert video document to dict using model_dump
            video_dict = video.model_dump()

            # Combine text for embedding
            combined_text = f"{video_dict['title']} {video_dict['description']} "
            if video_dict.get("transcript"):
                combined_text += " ".join(t["text"] for t in video_dict["transcript"])

            # Create vector with non-null metadata values
            metadata = {
                "text": combined_text,
                "title": video_dict["title"] or "",
                "description": video_dict["description"] or "",
                "thumbnails": video_dict["thumbnails"] or "",
            }

            vector = (
                video_dict["video_id"],
                embed.embed_query(combined_text),
                metadata,
            )
            vectors.append(vector)
            print(f"Processing video: {video_dict['video_id']}")
        except Exception as e:
            print(f"Error processing video: {e}")
            continue

    if not vectors:
        print("No vectors to upsert")
        return

    # Upsert vectors
    index = pc.Index(index_name)
    try:
        index.upsert(vectors=vectors)
        print(f"Successfully upserted {len(vectors)} vectors")
    except Exception as e:
        print(f"Error upserting vectors: {e}")
        return

    # Create embeddings and store in Pinecone
    vectorstore = PineconeVectorStore(
        text_key="text", embedding=embed, index_name=index_name
    )

    query = "What is growthX?"

    documents = vectorstore.similarity_search(query, k=3)  # return 3 most relevant docs

    print(f"\nQuery: {query}")
    for doc in documents:
        pprint(doc.__dict__)
        print()


def retrivalQAFunciton():
    """Test retrieval QA functionality"""
    index_name = "videos-index"
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY, model_name="gpt-4o", temperature=0.0
    )

    vectorstore = PineconeVectorStore(
        text_key="text", embedding=embed, index_name=index_name
    )

    qa = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever()
    )

    res = qa.invoke("Tell me 2 key points about growthX")

    print(res)

    # pc.delete_index(name=index_name)


if __name__ == "__main__":
    # Setup test index
    # setup_test_index("videos-index")

    # # Run basic operations test
    # asyncio.run(test_basic_operations())
    retrivalQAFunciton()
