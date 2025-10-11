# Changelog

## Version 1.1.0 - 2025-10-11

### Fixed

#### Backend Fixes

1. **Pydantic Validation Error with LLM Responses**
   - **Issue**: `ValidationError: Input should be a valid string [type=string_type, input_value=[...], input_type=list]`
   - **Root Cause**: VertexAI LLM was returning list responses instead of strings in some cases
   - **Solution**: Created `VertexAIWrapper` class that extends `VertexAI` and overrides `_call()` method to ensure string output
   - **Location**: `agent/developer_agent.py`
   - **Impact**: Agent now handles all LLM response types correctly

2. **PROJECT_ROOT Configuration**
   - **Issue**: Pydantic error when using `os.getenv('PROJECT_ROOT')`
   - **Solution**: Properly configured PROJECT_ROOT in `main.py` with absolute path resolution
   - **Location**: `main.py` lines 25-27
   - **Impact**: Agent can now work with custom project directories from `.env` file

3. **Output Parser Enhancement**
   - Added list-to-string conversion in `CustomOutputParser.parse()` as a fallback
   - Ensures robust handling of unexpected LLM output formats
   - **Location**: `agent/developer_agent.py` lines 236-241

### Added

#### Frontend Migration to TypeScript

1. **TypeScript Configuration**
   - Added `tsconfig.json` with strict type checking
   - Added `tsconfig.node.json` for Vite configuration
   - Updated `package.json` to include TypeScript dependency

2. **Converted Files to TypeScript**
   - `main.jsx` → `main.tsx`
   - `App.jsx` → `App.tsx`
   - `vite.config.js` → `vite.config.ts`
   - Added comprehensive type definitions for all components and API responses

3. **Type Safety Improvements**
   - Defined interfaces for:
     - `Message` - Chat message structure
     - `ThoughtStep` - Agent reasoning step
     - `QueryResponse` - API query response
     - `SessionCreateResponse` - Session creation response
     - `HistoryResponse` - Chat history response
   - Added proper typing for all React hooks and event handlers
   - Type-safe Axios error handling

### Technical Details

#### VertexAIWrapper Implementation

```python
class VertexAIWrapper(VertexAI):
    """Wrapper around VertexAI that ensures string output."""
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the VertexAI API and ensure string output."""
        result = super()._call(prompt, stop, run_manager, **kwargs)
        
        # Handle list responses
        if isinstance(result, list):
            result = ' '.join(str(item) for item in result)
        
        # Ensure string output
        return str(result)
```

This wrapper:
- Extends the base `VertexAI` class properly
- Overrides the `_call` method to intercept responses
- Converts list responses to strings before returning
- Maintains compatibility with LangChain's validation

#### TypeScript Benefits

1. **Compile-time Error Detection**: Catch type errors before runtime
2. **Better IDE Support**: Improved autocomplete and IntelliSense
3. **Self-documenting Code**: Type definitions serve as documentation
4. **Refactoring Safety**: Type system helps prevent breaking changes
5. **Better Developer Experience**: Clear contracts between components

### Migration Guide

#### For Existing Installations

1. **Update Python Dependencies** (if needed):
   ```bash
   pip install --upgrade langchain langchain-google-vertexai
   ```

2. **Update UI Dependencies**:
   ```bash
   cd ui
   npm install
   ```

3. **No Configuration Changes Required**: The `.env` file format remains the same

#### For New Installations

Follow the updated `SETUP_GUIDE.md` which includes TypeScript setup.

### Breaking Changes

None. All changes are backward compatible.

### Known Issues

None at this time.

### Performance Improvements

- TypeScript compilation adds minimal overhead
- VertexAIWrapper has negligible performance impact
- Type checking happens at build time, not runtime

### Testing

Tested scenarios:
- ✅ Simple file operations (create, read, update, delete)
- ✅ Complex multi-step operations
- ✅ Large file handling
- ✅ Session management
- ✅ Error handling and recovery
- ✅ List response handling from LLM
- ✅ TypeScript compilation and type checking

### Documentation Updates

- Updated `README.md` with TypeScript information
- Updated `ui/README.md` to reflect TypeScript migration
- Updated `TROUBLESHOOTING.md` with new error scenarios
- Created this `CHANGELOG.md`

### Contributors

- Fixed LLM validation errors
- Migrated UI to TypeScript
- Enhanced error handling
- Improved type safety

---

## Version 1.0.0 - 2025-10-11

Initial release with:
- LangChain-based developer agent
- Session-based chat system
- React UI with thought process viewer
- File operation tools
- GCP Vertex AI integration
- Application Default Credentials support
