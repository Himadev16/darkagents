"""
File Extractor - Advanced Multi-Pattern File Extraction
Extracts code files from LLM responses with 6+ pattern support and fallback mechanisms
"""
import re
from typing import Dict
from pathlib import Path
import structlog

logger = structlog.get_logger()


class FileExtractor:
    """
    Extracts code files from LLM responses using multiple pattern matching strategies

    Supports 6+ extraction patterns:
    1. Hash Path: # Path: filepath
    2. Slash Path: // Path: filepath
    3. Block Path: /* Path: filepath */
    4. SQL Path: -- Path: filepath
    5. Markdown Code: ```language\n# Path: filepath
    6. File Comment: # File: filepath

    Features:
    - Multiple pattern matching
    - Fallback extraction for edge cases
    - Auto file extension guessing
    - Duplicate file handling
    - Code cleaning and validation
    """

    PATTERNS = {
        'hash_path': r'#\s*Path:\s*([^\n]+)\n(.*?)(?=(?:#\s*Path:|$))',
        'slash_path': r'//\s*Path:\s*([^\n]+)\n(.*?)(?=(?://\s*Path:|$))',
        'block_path': r'/\*\s*Path:\s*([^\n]+)\s*\*/\n(.*?)(?=(?:/\*\s*Path:|$))',
        'sql_path': r'--\s*Path:\s*([^\n]+)\n(.*?)(?=(?:--\s*Path:|$))',
        'markdown_code': r'```(?:[\w]+)?\n#\s*Path:\s*([^\n]+)\n(.*?)```',
        'file_comment': r'#\s*File:\s*([^\n]+)\n(.*?)(?=(?:#\s*File:|$))'
    }

    def __init__(self):
        self.extracted_count = 0
        logger.info("FileExtractor initialized with 6+ patterns")

    def extract_files(self, response: str) -> Dict[str, str]:
        """
        Parse multi-file code blocks from LLM response

        Args:
            response: Raw LLM response text

        Returns:
            Dictionary of filepath -> code content
        """
        files = {}

        if not response:
            logger.warning("Empty response received")
            return files

        # Try all patterns
        for pattern_name, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, response, re.DOTALL | re.MULTILINE)

            for filepath, code in matches:
                filepath = self._clean_filepath(filepath)
                code = self._clean_code(code)

                if filepath and code:
                    if filepath in files:
                        logger.warning(f"Duplicate file found: {filepath}")
                        # Keep the longer/more complete version
                        if len(code) > len(files[filepath]):
                            files[filepath] = code
                            logger.debug(f"Updated {filepath} with longer version")
                    else:
                        files[filepath] = code
                        logger.debug(f"Extracted: {filepath} ({len(code)} chars) using {pattern_name}")

        self.extracted_count = len(files)

        if self.extracted_count == 0:
            logger.error("No files extracted from response using standard patterns")
            self._attempt_fallback_extraction(response, files)

        logger.info(f"Extracted {len(files)} files from response")
        return files

    def _clean_filepath(self, filepath: str) -> str:
        """
        Clean and validate filepath

        Args:
            filepath: Raw filepath string

        Returns:
            Cleaned filepath or empty string if invalid
        """
        if not filepath:
            return ""

        # Remove quotes, backticks, whitespace
        filepath = filepath.strip().strip('"\'`')
        filepath = filepath.replace('```', '').strip()

        # Security: reject paths with ../ or absolute paths
        if not filepath or '..' in filepath or filepath.startswith('/'):
            logger.warning(f"Invalid filepath rejected: {filepath}")
            return ""

        path = Path(filepath)

        # Add extension if missing
        if not path.suffix:
            logger.warning(f"File without extension: {filepath}")
            # Guess extension based on filename
            if 'component' in filepath.lower() or 'app' in filepath.lower():
                filepath += '.tsx'
            elif 'style' in filepath.lower() or 'css' in filepath.lower():
                filepath += '.css'
            elif 'test' in filepath.lower():
                filepath += '.test.ts'
            elif 'api' in filepath.lower() or 'route' in filepath.lower():
                filepath += '.py'
            elif 'model' in filepath.lower() or 'schema' in filepath.lower():
                filepath += '.py'
            else:
                filepath += '.py'  # Default to Python
            logger.debug(f"Added extension: {filepath}")

        return filepath

    def _clean_code(self, code: str) -> str:
        """
        Clean extracted code

        Args:
            code: Raw code string

        Returns:
            Cleaned code
        """
        if not code:
            return ""

        code = code.strip()

        # Remove path comment if it leaked into code
        lines = code.split('\n')
        if lines and lines[0].startswith(('#', '//', '/*', '--')):
            if 'Path:' in lines[0] or 'File:' in lines[0]:
                lines = lines[1:]
                code = '\n'.join(lines).strip()

        # Remove markdown code block markers
        code = re.sub(r'^```[\w]*\n?', '', code)
        code = re.sub(r'\n?```$', '', code)

        return code

    def _attempt_fallback_extraction(self, response: str, files: Dict):
        """
        Attempt fallback extraction for edge cases

        This method handles responses that don't match standard patterns
        """
        logger.info("Attempting fallback extraction...")

        # Extract all code blocks
        code_blocks = re.findall(r'```(?:[\w]+)?\n(.*?)```', response, re.DOTALL)

        for i, block in enumerate(code_blocks):
            lines = block.split('\n')[:5]  # Check first 5 lines
            filepath = None

            # Look for filepath in first few lines
            for line in lines:
                # Check if line looks like a filepath
                if re.match(r'^[a-zA-Z0-9_/.-]+\.[a-zA-Z0-9]+$', line.strip()):
                    filepath = line.strip()
                    break
                # Check for file: or path: mentions
                elif 'file:' in line.lower() or 'path:' in line.lower():
                    match = re.search(r'(?:file|path):\s*([^\n]+)', line, re.IGNORECASE)
                    if match:
                        filepath = self._clean_filepath(match.group(1))
                        break

            if filepath:
                # Extract code, removing the filepath line
                code = '\n'.join(l for l in block.split('\n') if filepath not in l)
                code = self._clean_code(code)
                if code:
                    files[filepath] = code
                    logger.info(f"Fallback extracted: {filepath}")
            else:
                # Generate filename based on content
                ext = self._guess_extension(block)
                filepath = f"extracted_file_{i+1}.{ext}"
                code = self._clean_code(block)
                if code:
                    files[filepath] = code
                    logger.warning(f"Generated filename: {filepath}")

    def _guess_extension(self, code: str) -> str:
        """
        Guess file extension from code content

        Args:
            code: Code content

        Returns:
            File extension (without dot)
        """
        code_lower = code.lower()

        # Check for language-specific patterns
        if 'import react' in code_lower or 'jsx' in code_lower or 'export default' in code_lower:
            return 'tsx' if 'interface' in code_lower or 'type ' in code_lower else 'jsx'
        elif 'function' in code_lower and ('const' in code_lower or 'let' in code_lower):
            return 'js'
        elif 'def ' in code_lower or 'import ' in code_lower or 'from ' in code_lower:
            return 'py'
        elif 'select' in code_lower or 'create table' in code_lower or 'insert into' in code_lower:
            return 'sql'
        elif '{' in code and '}' in code and ';' in code and ('color' in code_lower or 'font' in code_lower):
            return 'css'
        elif '<html' in code_lower or '<div' in code_lower or '<body' in code_lower:
            return 'html'
        elif 'dockerfile' in code_lower or 'from ' in code_lower and 'run ' in code_lower:
            return 'dockerfile'
        elif 'version:' in code_lower and ('services:' in code_lower or 'image:' in code_lower):
            return 'yml'
        else:
            return 'txt'

    def validate_extraction(self, files: Dict[str, str]) -> Dict:
        """
        Validate extraction quality

        Returns:
            Validation report
        """
        report = {
            'total_files': len(files),
            'files_with_content': 0,
            'average_file_size': 0,
            'extensions': {},
            'quality_score': 0.0
        }

        if not files:
            return report

        total_size = 0
        for filepath, code in files.items():
            if code and len(code) > 10:  # At least 10 characters
                report['files_with_content'] += 1
                total_size += len(code)

            # Count extensions
            ext = Path(filepath).suffix
            report['extensions'][ext] = report['extensions'].get(ext, 0) + 1

        if report['files_with_content'] > 0:
            report['average_file_size'] = total_size // report['files_with_content']

        # Calculate quality score (0-100)
        if report['total_files'] > 0:
            content_ratio = report['files_with_content'] / report['total_files']
            size_score = min(report['average_file_size'] / 1000, 1.0)  # Max at 1000 chars
            variety_score = min(len(report['extensions']) / 3, 1.0)  # Max at 3 different types

            report['quality_score'] = (content_ratio * 0.5 + size_score * 0.3 + variety_score * 0.2) * 100

        logger.info(f"Extraction quality score: {report['quality_score']:.1f}/100")

        return report


# Singleton instance
file_extractor = FileExtractor()
