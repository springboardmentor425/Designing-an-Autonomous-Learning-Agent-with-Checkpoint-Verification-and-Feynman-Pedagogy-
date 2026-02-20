"""Learning Agent with User Clarification and Adaptive Quiz System.

This module implements:
1. Auto-loading reports from the files directory
2. User clarification to generate a detailed research brief
3. Checkpoint-based learning with quizzes and remediation
"""

import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Annotated, Literal, Optional, Sequence
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, get_buffer_string

from deep_research_from_scratch.prompts import clarify_with_user_instructions, transform_messages_into_research_topic_prompt
from deep_research_from_scratch.state_scope import ClarifyWithUser, ResearchQuestion
from deep_research_from_scratch.retry_utils import invoke_with_retry

# --- 1. SETUP MODEL ---
# Using llama-3.1-8b-instant for chat, llama-3.3-70b-versatile for structured output (better function calling)
model = init_chat_model("groq:llama3-8b-8192")
structured_model = init_chat_model("groq:llama-3.3-70b-versatile")


# --- 2. UTILITY FUNCTIONS ---

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    try:
        return datetime.now().strftime("%a %b %#d, %Y")
    except ValueError:
        return datetime.now().strftime("%a %b %-d, %Y")


# --- 3. DEFINE STATE SCHEMAS ---

class Checkpoint(TypedDict):
    id: str
    name: str
    objective: str
    # Content fields (populated by Node 2)
    study_material: str 
    quiz_questions: list[str]
    # User Interaction fields (populated by Node 3)
    user_answers: list[str]
    # Evaluation fields (populated by Node 4)
    score: int
    passed: bool
    feedback: str
    # Simplified teaching fields (populated by Node 5)
    simplified_material: str


class State(TypedDict):
    # Report loaded from files directory
    report: str
    # Messages for user clarification
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # Research brief generated from clarification (becomes user_request)
    research_brief: Optional[str]
    user_request: str
    # Learning checkpoints
    checkpoints: list[Checkpoint]
    current_checkpoint_index: int


class InputState(TypedDict):
    """Input state - user only provides messages."""
    messages: Annotated[Sequence[BaseMessage], add_messages] 

# --- 4. DEFINE PYDANTIC MODELS (LLM INTERFACE) ---

# Schema for Node 1 (Structure)
class CheckpointItem(BaseModel):
    name: str = Field(description="Name of the checkpoint")
    objective: str = Field(description="Objective of the checkpoint")

class CheckpointResponse(BaseModel):
    checkpoints: List[CheckpointItem]

# Schema for Node 2 (Content)
class CheckpointContent(BaseModel):
    study_material: str = Field(description="Brief study material (approx 100 words)")
    quiz_questions: List[str] = Field(description="Exactly 3 assessment questions")

# Schema for Node 4 (Evaluation)
class EvaluationResult(BaseModel):
    score: int = Field(description="Score out of 100")
    feedback: str = Field(description="Constructive feedback for the student")
    passed: bool = Field(description="True if score >= 70, False if failed")

# Schema for Node 5 (Simplified Teaching - Feynman Technique)
class SimplifiedContent(BaseModel):
    simplified_material: str = Field(description="Simple explanation using Feynman Technique (short, plain language, no jargon)")

# Create Structured LLMs — using Gemini for reliable function calling
structure_gen = structured_model.with_structured_output(CheckpointResponse)
content_gen = structured_model.with_structured_output(CheckpointContent)
evaluator_gen = structured_model.with_structured_output(EvaluationResult)
simplified_gen = structured_model.with_structured_output(SimplifiedContent)


# --- 5. DEFINE NODES ---

def load_report(state: State):
    """Node 0: Finds the most relevant report for the user's topic, or falls back to latest."""
    print("--- Loading Report from Files Directory ---")
    
    # Get the files directory path (relative to this module)
    files_dir = Path(__file__).parent / "files"
    
    if not files_dir.exists():
        raise FileNotFoundError(f"Files directory not found: {files_dir}")
    
    # Find all markdown files
    md_files = list(files_dir.glob("*.md"))
    
    if not md_files:
        raise FileNotFoundError(f"No markdown files found in: {files_dir}")
    
    # Extract user's topic keywords from the first human message
    user_topic = ""
    for msg in state.get("messages", []):
        if hasattr(msg, "type") and msg.type == "human":
            user_topic = msg.content.lower()
            break
        elif isinstance(msg, dict) and msg.get("role") == "human":
            user_topic = msg.get("content", "").lower()
            break
    
    # Try to find the most relevant report by scanning file content (first 500 chars)
    best_file = None
    best_score = 0
    
    if user_topic:
        # Extract meaningful keywords (words > 3 chars, skip common words)
        stop_words = {"what", "about", "tell", "me", "want", "learn", "explain", "please", "can", "you", "the", "and", "for", "how", "does", "is", "are", "will", "would", "that", "this", "with"}
        keywords = [w for w in user_topic.split() if len(w) > 3 and w not in stop_words]
        
        if keywords:
            for f in md_files:
                try:
                    preview = f.read_text(encoding="utf-8")[:500].lower()
                    score = sum(1 for kw in keywords if kw in preview)
                    if score > best_score:
                        best_score = score
                        best_file = f
                except Exception:
                    continue
    
    # Fall back to most recently modified file if no keyword match found
    if best_file is None or best_score == 0:
        best_file = max(md_files, key=lambda f: f.stat().st_mtime)
        print(f"No topic match found. Loading latest file: {best_file.name}")
    else:
        print(f"Best topic match (score={best_score}): {best_file.name}")
    
    # Read the file content
    report_content = best_file.read_text(encoding="utf-8")
    
    return {"report": report_content}


def clarify_with_user(state: State) -> Command[Literal["write_research_brief", "__end__"]]:
    """
    Determine if the user's request contains sufficient information to proceed.
    
    Uses structured output to make deterministic decisions and avoid hallucination.
    Routes to either research brief generation or ends with a clarification question.
    """
    print("--- Clarifying with User ---")
    

    
    # Set up structured output model
    structured_output_model = model.with_structured_output(ClarifyWithUser)
    
    # Invoke the model with clarification instructions
    response = invoke_with_retry(structured_output_model, [
        HumanMessage(content=clarify_with_user_instructions.format(
            messages=get_buffer_string(messages=state["messages"]), 
            date=get_today_str()
        ))
    ])
    
    # Route based on clarification need
    if response.need_clarification:
        print(f"Need clarification: {response.question}")
        return Command(
            goto=END, 
            update={"messages": [AIMessage(content=response.question)]}
        )
    else:
        print("Sufficient info, proceeding to write research brief")
        return Command(
            goto="write_research_brief", 
            update={"messages": [AIMessage(content=response.verification)]}
        )


def write_research_brief(state: State):
    """
    Transform the conversation history into a comprehensive research brief.
    
    The research_brief becomes the user_request for the learning pipeline.
    """
    print("--- Writing Research Brief ---")
    
    # Set up structured output model
    structured_output_model = model.with_structured_output(ResearchQuestion)
    
    # Generate research brief from conversation history
    response = structured_output_model.invoke([
        HumanMessage(content=transform_messages_into_research_topic_prompt.format(
            messages=get_buffer_string(state.get("messages", [])),
            date=get_today_str()
        ))
    ])
    
    print(f"Research brief: {response.research_brief[:100]}...")
    
    # Map research_brief to user_request for the learning pipeline
    return {
        "research_brief": response.research_brief,
        "user_request": response.research_brief
    }


def generate_structure(state: State):
    """Node 1: Breaks the report down into topics (No content yet)."""
    print("--- Generating Structure ---")
    report = state['report']
    # Truncate report to avoid token limits on structured output calls
    report_excerpt = report[:4000] if len(report) > 4000 else report
    response = structure_gen.invoke(f"Extract 3-5 key learning checkpoints from this research report. Each checkpoint should be a distinct topic or concept.\n\nReport:\n{report_excerpt}")
    
    clean_checkpoints = []
    for item in response.checkpoints:
        data = item.model_dump()
        # Initialize Defaults
        data['id'] = str(uuid.uuid4())
        data['study_material'] = ""
        data['quiz_questions'] = []
        data['user_answers'] = []
        data['score'] = 0
        data['passed'] = False
        data['feedback'] = ""
        data['simplified_material'] = ""
        
        clean_checkpoints.append(data)
        
    return {"checkpoints": clean_checkpoints, "current_checkpoint_index": 0}


def create_content(state: State):
    """Node 2: Generates study material and questions in PARALLEL (Batch)."""
    print("--- Creating Content (Batch) ---")
    report = state['report']
    user_req = state['user_request']
    checkpoints = state['checkpoints']
    
    updated_checkpoints = []
    
    # Process checkpoints sequentially with retry logic to avoid rate limits and improve robustness
    for cp in checkpoints:
        prompt = f"""You are creating educational content for a learning checkpoint.

Report Context: {report}
User Goal: {user_req}

Checkpoint Details:
- Name: {cp['name']}
- Objective: {cp['objective']}

REQUIREMENTS:
1. Create a clear, concise study material (approximately 100 words) that explains the key concepts of this checkpoint
2. Create EXACTLY 3 assessment questions that test understanding of the study material

IMPORTANT:
- Ensure the questions directly relate to the study material provided.
- Do not provide answers, just the questions.
"""
        try:
            # Use invoke_with_retry for robustness
            res = invoke_with_retry(content_gen, prompt)
            
            cp['study_material'] = res.study_material
            cp['quiz_questions'] = res.quiz_questions
            updated_checkpoints.append(cp)
            
        except Exception as e:
            print(f"Error generating content for checkpoint '{cp['name']}': {e}")
            # Fallback for failed generation
            cp['study_material'] = "Content generation failed. Please refer to the full report."
            cp['quiz_questions'] = ["What is the main topic of this section?", "List three key points.", "Summarize the content."]
            updated_checkpoints.append(cp)
        
    return {"checkpoints": updated_checkpoints}


def administer_quiz(state: State):
    """Node 3: Pauses graph to show content and wait for user answers."""
    idx = state.get("current_checkpoint_index", 0)
    checkpoints = state["checkpoints"]
    
    if idx >= len(checkpoints):
        return {} # Safety catch

    current_cp = checkpoints[idx]
    
    print(f"--- Administering Quiz: {current_cp['name']} ---")

    # Use simplified material if available (after remediation), otherwise use original
    material = current_cp['simplified_material'] if current_cp['simplified_material'] else current_cp['study_material']

    # Prepare Payload for UI/User
    user_view = {
        "title": current_cp["name"],
        "material": material,
        "questions": current_cp["quiz_questions"]
    }

    # *** INTERRUPT ***
    # The graph STOPS here. Resume with: graph.invoke(Command(resume=answers_list))
    user_answers = interrupt(user_view)
    
    # Resume Logic
    current_cp["user_answers"] = user_answers
    checkpoints[idx] = current_cp
    
    return {"checkpoints": checkpoints}


def evaluate_submission(state: State):
    """Node 4: Grades the quiz and decides next steps."""
    print("--- Evaluating Submission ---")
    idx = state["current_checkpoint_index"]
    checkpoints = state["checkpoints"]
    current_cp = checkpoints[idx]
    
    # Evaluate
    prompt = f"""
    Topic: {current_cp['name']}
    Questions: {current_cp['quiz_questions']}
    Answers: {current_cp['user_answers']}
    Rubric: Pass mark is 70.
    """
    result = evaluator_gen.invoke(prompt)
    
    # Save Result
    current_cp["score"] = result.score
    current_cp["passed"] = result.passed
    current_cp["feedback"] = result.feedback
    checkpoints[idx] = current_cp
    
    # Decide Index Movement
    next_idx = idx
    if result.passed:
        print(f"PASSED ({result.score}). Moving to next topic.")
        next_idx = idx + 1
    else:
        print(f"FAILED ({result.score}). Retrying same topic.")
        # next_idx stays the same
        
    return {"checkpoints": checkpoints, "current_checkpoint_index": next_idx}


def simplified_teaching(state: State):
    """Node 5: Remedial teaching using Feynman Technique (Simple Explanations)."""
    print("--- Simplified Teaching Mode (Feynman Technique) ---")
    idx = state["current_checkpoint_index"]
    checkpoints = state["checkpoints"]
    current_cp = checkpoints[idx]
    
    # Create a Feynman-style explanation based on what the student struggled with
    prompt = f"""The student struggled with this topic. Use the FEYNMAN TECHNIQUE to create a MUCH SIMPLER explanation.
    
Topic: {current_cp['name']}
Original Explanation: {current_cp['study_material']}

Questions Asked:
{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(current_cp['quiz_questions'])])}

Student's Answers:
{chr(10).join([f"{i+1}. {a}" for i, a in enumerate(current_cp['user_answers'])])}

Feedback on Their Answers: {current_cp['feedback']}

FEYNMAN TECHNIQUE RULES:
1. Use ONLY simple, everyday language - avoid all technical jargon
2. Explain as if talking to a 10-year-old
3. Use analogies and real-world examples
4. Break complex ideas into simple parts
5. Be very short and concise
6. Focus on the core concept the student got wrong

Create a simplified explanation that helps the student understand the concept:"""
    
    result = simplified_gen.invoke(prompt)
    
    # Save the simplified material
    current_cp["simplified_material"] = result.simplified_material
    checkpoints[idx] = current_cp
    
    print(f"Simplified material generated for retry")
    
    return {"checkpoints": checkpoints}


# --- 6. ROUTING LOGIC ---

def decide_next_step(state: State) -> Literal["administer_quiz", "simplified_teaching", END]:
    idx = state["current_checkpoint_index"]
    checkpoints = state["checkpoints"]
    
    # 1. Done?
    if idx >= len(checkpoints):
        print("--- All Checkpoints Completed ---")
        return END
        
    # 2. Failed? (Check current index status)
    current_cp = checkpoints[idx]
    # If we have a score but passed is False, we need help
    if "passed" in current_cp and current_cp["passed"] is False:
        return "simplified_teaching"
        
    # 3. Ready for Quiz (New topic or retry)
    return "administer_quiz"


# --- 7. BUILD GRAPH ---

builder = StateGraph(State, input=InputState)

# Add Nodes
builder.add_node("load_report", load_report)
builder.add_node("clarify_with_user", clarify_with_user)
builder.add_node("write_research_brief", write_research_brief)
builder.add_node("generate_structure", generate_structure)
builder.add_node("create_content", create_content)
builder.add_node("administer_quiz", administer_quiz)
builder.add_node("evaluate_submission", evaluate_submission)
builder.add_node("simplified_teaching", simplified_teaching)

# Add Edges
builder.add_edge(START, "load_report")
builder.add_edge("load_report", "clarify_with_user")
# clarify_with_user uses Command() to route to write_research_brief or END
builder.add_edge("write_research_brief", "generate_structure")
builder.add_edge("generate_structure", "create_content")
builder.add_edge("create_content", "administer_quiz")  # Start 1st quiz
builder.add_edge("administer_quiz", "evaluate_submission")
builder.add_edge("simplified_teaching", "administer_quiz")  # Retry loop

# Add Conditional Edge
builder.add_conditional_edges(
    "evaluate_submission",
    decide_next_step,
    {
        "administer_quiz": "administer_quiz",
        "simplified_teaching": "simplified_teaching",
        END: END
    }
)

learning_agent = builder.compile()

