import time

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
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate_limit" in error_str.lower() or "rate limit" in error_str.lower():
                if attempt < max_retries - 1:
                    # Short backoff: 5s, 10s, 20s max
                    wait_time = 5 * (2 ** attempt)
                    print(f"Rate limited. Waiting {wait_time}s before retry... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print("Quota exhausted after all retries.")
                    raise
            else:
                raise


async def ainvoke_with_retry(model, messages, max_retries=3):
    """
    Async version: Invoke model with exponential backoff retry for rate limiting.
    
    Args:
        model: The model to invoke
        messages: Messages to send to the model
        max_retries: Maximum number of retry attempts
        
    Returns:
        Model response
    """
    import asyncio
    for attempt in range(max_retries):
        try:
            return await model.ainvoke(messages)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate_limit" in error_str.lower() or "rate limit" in error_str.lower():
                if attempt < max_retries - 1:
                    # Short backoff: 5s, 10s, 20s max
                    wait_time = 5 * (2 ** attempt)
                    print(f"Rate limited. Waiting {wait_time}s before retry... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    print("Quota exhausted after all retries.")
                    raise
            else:
                raise

