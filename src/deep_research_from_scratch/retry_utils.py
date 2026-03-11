import time
import random
import re

def invoke_with_retry(model, messages, max_retries=3):
    """
    Invoke model with exponential backoff retry for rate limiting.
    
    Args:
        model: The structured output model to invoke
        messages: Messages to send to the model
        max_retries: Maximum number of retry attempts
        
    Returns:
        Model response
    """
    for attempt in range(max_retries):
        try:
            return model.invoke(messages)

        except Exception as e:
            error_str = str(e).lower()

            if "429" in error_str or "resource_exhausted" in error_str or "rate_limit" in error_str:

                if attempt < max_retries - 1:

                    match = re.search(r"try again in ([0-9.]+)s", error_str)

                    if match:
                        wait_time = float(match.group(1))
                    else:
                        wait_time = (5 * (2 ** attempt)) + random.uniform(0, 2)

                    print(f"Rate limited. Waiting {wait_time:.2f}s (attempt {attempt+1})")
                    time.sleep(wait_time)

                else:
                    print("Quota exhausted after all retries.")
                    raise
            else:
                raise


import asyncio

async def ainvoke_with_retry(model, messages, max_retries=5):
    """
    Async version: Invoke model with exponential backoff retry for rate limiting.
    
    Args:
        model: The model to invoke
        messages: Messages to send to the model
        max_retries: Maximum number of retry attempts
        
    Returns:
        Model response
    """
    for attempt in range(max_retries):
        try:
            return await model.ainvoke(messages)

        except Exception as e:
            error_str = str(e).lower()

            if "429" in error_str or "resource_exhausted" in error_str or "rate_limit" in error_str:

                if attempt < max_retries - 1:

                    match = re.search(r"try again in ([0-9.]+)s", error_str)

                    if match:
                        wait_time = float(match.group(1))
                    else:
                        wait_time = (5 * (2 ** attempt)) + random.uniform(0, 2)

                    print(f"Rate limited. Waiting {wait_time:.2f}s (attempt {attempt+1})")

                    await asyncio.sleep(wait_time)

                else:
                    print("Quota exhausted after all retries.")
                    raise
            else:
                raise