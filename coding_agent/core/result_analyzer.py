
class ResultAnalyzer:
    """
    Analyzes and compresses tool results to fit within the context budget.
    """

    def __init__(self, max_output_tokens: int = 1024):
        self.max_output_tokens = max_output_tokens

    def _truncate_text(self, text: str, max_len: int) -> str:
        """Truncates text to a maximum length, showing the beginning and end."""
        if len(text) <= max_len:
            return text
        
        half_len = (max_len - 50) // 2
        
        truncated_text = (
            f"{text[:half_len]}\n"
            f"[...content truncated...]\n"
            f"{text[-half_len:]}"
        )
        return truncated_text

    def compress(self, tool_output: any, tool_name: str) -> str:
        """
        Compresses the tool output based on the tool name.

        Args:
            tool_output: The raw output from the tool.
            tool_name: The name of the tool that produced the output.

        Returns:
            The compressed tool output as a string.
        """
        if tool_name == 'run_command' and isinstance(tool_output, dict):
            stdout = tool_output.get('stdout', '')
            stderr = tool_output.get('stderr', '')
            exit_code = tool_output.get('exit_code')

            # If total output is already small, return it as is but formatted.
            if len(stdout) + len(stderr) < self.max_output_tokens:
                return (
                    f"Command exited with code: {exit_code}\n"
                    f"--- STDOUT ---\n{stdout}\n"
                    f"--- STDERR ---\n{stderr}"
                )

            compressed_stdout = self._truncate_text(stdout, self.max_output_tokens // 2)
            compressed_stderr = self._truncate_text(stderr, self.max_output_tokens // 2)

            return (
                f"Command exited with code: {exit_code}\n"
                f"--- STDOUT ---\n{compressed_stdout}\n"
                f"--- STDERR ---\n{compressed_stderr}"
            )

        # Fallback for other tools or plain string output
        if not isinstance(tool_output, str):
            tool_output = str(tool_output)

        if len(tool_output) > self.max_output_tokens:
            summary = self._truncate_text(tool_output, self.max_output_tokens)
            return f"Tool output was too long and has been summarized.\n{summary}"

        return tool_output
