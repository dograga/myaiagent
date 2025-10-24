# Quick Start: File Attachment Feature

## For Users

### How to Attach Files

1. **Click the 📎 button** in the chat input area
2. **Select one or more files** from your computer
3. **See attached files** listed above the input box
4. **Remove files** by clicking the ✕ button next to each file
5. **Send your message** - files will be included automatically

### Supported File Types

- **Text files**: `.txt`, `.py`, `.js`, `.md`, `.json`, etc.
- **PDF files**: `.pdf` (text will be extracted)
- **Images**: `.jpg`, `.png`, `.gif`, etc. (for AI vision models)

### Tips

- You can attach multiple files at once
- Files are sent as base64-encoded data
- Large files may take longer to upload
- Attached files are cleared after sending

## For Developers

### Backend Setup

1. **Install dependencies** (optional):
   ```bash
   pip install PyPDF2  # For PDF support
   ```

2. **Start the backend**:
   ```bash
   python main.py
   # or
   uvicorn main:app --reload
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd ui
   npm install
   ```

2. **Start the dev server**:
   ```bash
   npm run dev
   ```

### Testing the Feature

1. Open the app in your browser
2. Create a new session
3. Click the 📎 button
4. Attach a test file (e.g., a `.txt` or `.py` file)
5. Type a message like "What's in this file?"
6. Click Send
7. The AI should respond with information about the file content

### Code Structure

```
myaiagent/
├── utils/
│   └── file_handler.py          # Backend file processing
├── ui/src/
│   ├── hooks/
│   │   └── useFileAttachment.ts # Frontend file logic
│   ├── components/
│   │   ├── FileAttachment.tsx   # File display component
│   │   └── ChatInput.tsx        # Updated with file support
│   └── App.tsx                  # Main app with file integration
└── main.py                      # API endpoints with file processing
```

### API Request Format

```json
{
  "query": "Your message here",
  "session_id": "session-id",
  "attached_files": [
    {
      "filename": "example.txt",
      "content": "base64_encoded_content"
    }
  ]
}
```

### Adding New File Types

**Backend** (`utils/file_handler.py`):
```python
SUPPORTED_FILE_TYPES = {
    'text': ['.txt', '.md', '.py', ...],
    'pdf': ['.pdf'],
    'image': ['.jpg', '.png', ...],
    'new_type': ['.ext1', '.ext2']  # Add here
}
```

**Frontend** (`ui/src/hooks/useFileAttachment.ts`):
```typescript
const ALLOWED_FILE_TYPES = [
  'text/*',
  'application/pdf',
  'image/*',
  'application/new-type'  // Add here
]
```

## Troubleshooting

### Issue: Files not attaching
**Solution**: Check browser console for errors, verify file type is supported

### Issue: PDF text not extracted
**Solution**: Install PyPDF2: `pip install PyPDF2`

### Issue: Large files failing
**Solution**: Check file size limits in frontend hook (default: 10MB)

### Issue: Temp files accumulating
**Solution**: Temp files should auto-cleanup. Check system temp directory and verify cleanup code is running

## Next Steps

- ✅ Feature is ready to use
- 📝 See `FILE_ATTACHMENT_IMPLEMENTATION.md` for detailed documentation
- 🧪 Run `test_file_attachment.py` for automated tests
- 🚀 Deploy and enjoy!
