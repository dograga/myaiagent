# File Attachment Feature - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                             │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                         App.tsx                               │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  useFileAttachment Hook                                 │  │  │
│  │  │  - attachedFiles: File[]                                │  │  │
│  │  │  - handleFileAttach()                                   │  │  │
│  │  │  - handleFileChange()                                   │  │  │
│  │  │  - removeFile()                                         │  │  │
│  │  │  - readAllFiles() → base64                             │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  │                           ↓                                   │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  ChatInput Component                                    │  │  │
│  │  │  ┌──────────────────────────────────────────────────┐  │  │  │
│  │  │  │  FileAttachment Component                         │  │  │  │
│  │  │  │  - Display attached files                         │  │  │  │
│  │  │  │  - Remove file buttons                            │  │  │  │
│  │  │  └──────────────────────────────────────────────────┘  │  │  │
│  │  │  - 📎 Attach button                                    │  │  │
│  │  │  - Text input                                           │  │  │
│  │  │  - Send button                                          │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
                    ┌───────────────────────────┐
                    │   API Request (JSON)      │
                    │  {                        │
                    │    query: "...",          │
                    │    attached_files: [      │
                    │      {                    │
                    │        filename: "...",   │
                    │        content: "base64"  │
                    │      }                    │
                    │    ]                      │
                    │  }                        │
                    └───────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND API                                  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      main.py                                  │  │
│  │                                                                │  │
│  │  POST /query or /query/stream                                 │  │
│  │       ↓                                                        │  │
│  │  process_attached_files(attached_files)                       │  │
│  │       ↓                                                        │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  For each file:                                         │  │  │
│  │  │  1. Validate file type                                  │  │  │
│  │  │  2. Decode base64                                       │  │  │
│  │  │  3. Save to temp file                                   │  │  │
│  │  │  4. Extract content:                                    │  │  │
│  │  │     - Text files → read as UTF-8                        │  │  │
│  │  │     - PDF files → extract text                          │  │  │
│  │  │     - Image files → prepare for AI                      │  │  │
│  │  │  5. Format into query                                   │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  │       ↓                                                        │  │
│  │  formatted_query = query + file_contents                      │  │
│  │       ↓                                                        │  │
│  │  agent.run(formatted_query)                                   │  │
│  │       ↓                                                        │  │
│  │  cleanup_temp_files()                                         │  │
│  │       ↓                                                        │  │
│  │  return response                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↑
                                    │
                    ┌───────────────────────────┐
                    │  utils/file_handler.py    │
                    │                           │
                    │  FileHandler class:       │
                    │  - validate_file_type()   │
                    │  - save_temp_file()       │
                    │  - extract_pdf_text()     │
                    │  - cleanup_temp_file()    │
                    └───────────────────────────┘
```

## Data Flow Diagram

```
┌──────────┐
│   USER   │
└────┬─────┘
     │ 1. Click 📎 button
     ↓
┌────────────────────┐
│  File Picker Opens │
└────┬───────────────┘
     │ 2. Select files
     ↓
┌─────────────────────────────┐
│  useFileAttachment Hook     │
│  - Validate file types      │
│  - Store File objects       │
│  - Display in UI            │
└────┬────────────────────────┘
     │ 3. User clicks Send
     ↓
┌─────────────────────────────┐
│  readAllFiles()             │
│  - Read each file           │
│  - Convert to base64        │
│  - Create FileData[]        │
└────┬────────────────────────┘
     │ 4. Send API request
     ↓
┌─────────────────────────────┐
│  apiClient.sendQuery()      │
│  - POST to /query           │
│  - Include attached_files   │
└────┬────────────────────────┘
     │ 5. Backend receives
     ↓
┌─────────────────────────────┐
│  process_attached_files()   │
│  - Decode base64            │
│  - Validate types           │
│  - Save to temp files       │
└────┬────────────────────────┘
     │ 6. Extract content
     ↓
┌─────────────────────────────┐
│  FileHandler methods        │
│  - extract_pdf_text()       │
│  - Read text files          │
│  - Prepare images           │
└────┬────────────────────────┘
     │ 7. Format query
     ↓
┌─────────────────────────────┐
│  formatted_query            │
│  = user_query + file_text   │
└────┬────────────────────────┘
     │ 8. Process with AI
     ↓
┌─────────────────────────────┐
│  agent.run(formatted_query) │
│  - AI processes query       │
│  - Includes file content    │
└────┬────────────────────────┘
     │ 9. Cleanup
     ↓
┌─────────────────────────────┐
│  cleanup_temp_files()       │
│  - Delete temp files        │
│  - Free resources           │
└────┬────────────────────────┘
     │ 10. Return response
     ↓
┌─────────────────────────────┐
│  Frontend displays response │
│  - Clear attached files     │
│  - Show AI response         │
└─────────────────────────────┘
```

## Component Interaction Diagram

```
Frontend Components:
┌─────────────────────────────────────────────────────────┐
│                       App.tsx                            │
│  ┌─────────────────┐  ┌──────────────────────────────┐ │
│  │ useFileAttachment│  │ useMessageStreaming          │ │
│  │ Hook             │  │ Hook                         │ │
│  └────────┬────────┘  └──────────┬───────────────────┘ │
│           │                       │                      │
│           ↓                       ↓                      │
│  ┌─────────────────┐  ┌──────────────────────────────┐ │
│  │ ChatInput        │  │ MessageList                  │ │
│  │ Component        │  │ Component                    │ │
│  │  ┌────────────┐ │  └──────────────────────────────┘ │
│  │  │FileAttach  │ │                                    │
│  │  │Component   │ │                                    │
│  │  └────────────┘ │                                    │
│  └─────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
                          ↕
                  ┌───────────────┐
                  │  apiClient.ts │
                  └───────────────┘
                          ↕
Backend Components:
┌─────────────────────────────────────────────────────────┐
│                      main.py                             │
│  ┌─────────────────────────────────────────────────────┐│
│  │ FastAPI Endpoints                                    ││
│  │  - POST /query                                       ││
│  │  - POST /query/stream                                ││
│  └────────────────┬────────────────────────────────────┘│
│                   │                                      │
│                   ↓                                      │
│  ┌─────────────────────────────────────────────────────┐│
│  │ process_attached_files()                             ││
│  │  - Orchestrates file processing                      ││
│  └────────────────┬────────────────────────────────────┘│
│                   │                                      │
│                   ↓                                      │
│  ┌─────────────────────────────────────────────────────┐│
│  │ utils/file_handler.py                                ││
│  │  - FileHandler.validate_file_type()                  ││
│  │  - FileHandler.save_temp_file()                      ││
│  │  - FileHandler.extract_pdf_text()                    ││
│  │  - FileHandler.cleanup_temp_file()                   ││
│  └────────────────┬────────────────────────────────────┘│
│                   │                                      │
│                   ↓                                      │
│  ┌─────────────────────────────────────────────────────┐│
│  │ Agent (Developer/DevOps/CloudArchitect)              ││
│  │  - Processes formatted query with file content       ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## File Type Processing Flow

```
┌──────────────┐
│  File Input  │
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────┐
│  Validate File Type                  │
│  (FileHandler.validate_file_type)    │
└──────┬───────────────────────────────┘
       │
       ├─────────────┬─────────────┬──────────────┐
       ↓             ↓             ↓              ↓
┌─────────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐
│ Text Files  │ │   PDF   │ │  Images  │ │ Unsupported  │
│ .txt, .py   │ │  .pdf   │ │.jpg, .png│ │   .exe, etc  │
│ .md, .json  │ │         │ │          │ │              │
└──────┬──────┘ └────┬────┘ └────┬─────┘ └──────┬───────┘
       │             │           │               │
       ↓             ↓           ↓               ↓
┌─────────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐
│ Read as     │ │ Extract │ │ Save for │ │ Return Error │
│ UTF-8 text  │ │ text    │ │ AI model │ │ Message      │
│             │ │(PyPDF2) │ │          │ │              │
└──────┬──────┘ └────┬────┘ └────┬─────┘ └──────────────┘
       │             │           │
       └─────────────┴───────────┘
                     │
                     ↓
       ┌──────────────────────────┐
       │ Format into Query        │
       │ "**Attached Files:**     │
       │  --- File: name ---      │
       │  [content]               │
       │  "                       │
       └──────────────────────────┘
```

## Error Handling Flow

```
┌──────────────────┐
│  File Operation  │
└────────┬─────────┘
         │
         ↓
    ┌────────┐
    │  Try   │
    └───┬────┘
        │
        ├──────────────────────────────────┐
        ↓                                  ↓
┌───────────────┐                  ┌──────────────┐
│   Success     │                  │    Error     │
└───────┬───────┘                  └──────┬───────┘
        │                                 │
        ↓                                 ↓
┌───────────────┐              ┌──────────────────────┐
│ Process file  │              │ Catch Exception      │
│ Return result │              │  - ValueError        │
└───────────────┘              │  - IOError           │
                               │  - Exception         │
                               └──────┬───────────────┘
                                      │
                                      ↓
                               ┌──────────────────────┐
                               │ Format Error Message │
                               │ "File: name (Error)" │
                               └──────┬───────────────┘
                                      │
                                      ↓
                               ┌──────────────────────┐
                               │ Continue Processing  │
                               │ Other Files          │
                               └──────────────────────┘
```

## Cleanup Flow

```
┌──────────────────────┐
│  File Processing     │
│  Complete            │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│  Try Cleanup Block   │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────────────┐
│  For each temp_file_path:    │
│  - FileHandler.cleanup()     │
│  - os.remove(temp_path)      │
└──────────┬───────────────────┘
           │
           ├─────────────────────┐
           ↓                     ↓
┌──────────────────┐   ┌─────────────────┐
│  Success         │   │  Error          │
│  - File deleted  │   │  - Log warning  │
│  - Continue      │   │  - Continue     │
└──────────────────┘   └─────────────────┘
           │                     │
           └─────────┬───────────┘
                     │
                     ↓
           ┌─────────────────────┐
           │  All Files Cleaned  │
           │  Return Response    │
           └─────────────────────┘
```

## State Management (Frontend)

```
useFileAttachment Hook State:
┌─────────────────────────────────────────┐
│  attachedFiles: File[]                  │
│  - Browser File objects                 │
│  - Used for display                     │
│  - Cleared after sending                │
└─────────────────────────────────────────┘
           │
           ↓ (when sending)
┌─────────────────────────────────────────┐
│  readAllFiles() → FileData[]            │
│  - filename: string                     │
│  - content: string (base64)             │
│  - Sent to backend                      │
└─────────────────────────────────────────┘
```

## Summary

This architecture provides:
- ✅ **Separation of Concerns**: UI, business logic, and data processing are separated
- ✅ **Modularity**: Each component has a single responsibility
- ✅ **Error Handling**: Errors are caught and handled at each level
- ✅ **Resource Management**: Temp files are always cleaned up
- ✅ **Type Safety**: TypeScript ensures type correctness
- ✅ **Scalability**: Easy to add new file types or processing methods
