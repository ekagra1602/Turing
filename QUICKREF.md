# AgentFlow - Quick Reference

## Launch

```bash
./start_basic.sh    # Fast click recording
./start_pro.sh      # Full interaction recording
```

## Workflow

1. **⏺ Record** - Start recording
2. **Do stuff** - Perform actions
3. **⏹ Stop** - Stop recording
4. **💾 Save** - Save to file
5. **▶ Play** - Replay it

## Permissions

System Preferences → Security & Privacy → Privacy → Accessibility → Add Terminal

## Troubleshooting

```bash
# Fix coordinate issues
./venv_gui/bin/python tools/calibrate.py

# Check setup
./venv_gui/bin/python tools/diagnose.py
```

## Files

```
agentflow/
├── start_basic.sh    # Basic launcher
├── start_pro.sh      # Pro launcher
├── src/              # Source code
├── tools/            # Utilities
├── docs/             # Documentation
└── archive/          # Old files
```

## Basic vs Pro

| Feature | Basic | Pro |
|---------|-------|-----|
| Speed | ⚡ | 🐌 |
| Clicks | ✅ | ✅ |
| Movements | ❌ | ✅ |
| Keyboard | ❌ | ✅ |
| File Size | 2KB | 50KB |

## Tips

- First time? Use **Basic**
- Form filling? Use **Pro** + keyboard
- Fast automation? **Basic** + instant mode
- Tutorial/demo? **Pro** + smooth mode

## More Help

- `README.md` - Full documentation
- `docs/` - Detailed guides
- Issues? Check `docs/PERMISSIONS_FIX.md`

---

**Questions? Read the README!** 📖
