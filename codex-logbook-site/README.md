# Codex Logbook Site

This is the static site for hosting shared Codex Logbook dashboards and the public gallery on codex-logbook.dev.

## Structure

```
codex-logbook-site/
├── index.html              # Landing page with public gallery
├── admin.html              # Admin dashboard for managing gallery
├── share-template.html     # Template for shared dashboards
├── share.html              # Generated file (built from template by build.py)
├── build.py                # Build script to bundle assets from codex_logbook package
├── package.json            # Node.js configuration (convenience scripts)
│
├── static/                 # Static assets
│   ├── css/
│   │   ├── style.css      # Main site and gallery styles
│   │   └── admin.css      # Admin dashboard styles
│   └── js/
│       ├── gallery.js     # Gallery functionality
│       ├── share-viewer.js # Renders shared dashboards
│       └── admin.js       # Admin dashboard functionality
│
├── functions/              # Cloudflare Pages Functions
│   └── share/
│       └── [[id]].js      # Dynamic route handler for shares
│
└── Development servers (local testing only):
    ├── gallery-site-server.py     # Production-like server
    ├── local-dev-gallery-server.py # Development gallery server
    └── local-dev-share-server.py   # Development share viewer server
```

## How it Works

### 1. Build Process
During Cloudflare Pages build, `build.py` runs to:
- Import CSS from `codex_logbook/static/css/dashboard.css`
- Import JS modules from `codex_logbook/static/js/` (constants, utils, stats, charts, etc.)
- Bundle everything into a self-contained `share.html`
- This allows shared dashboards to work without the main Codex Logbook server

### 2. Share Viewing
When someone visits `codex-logbook.dev/share/abc123`:
- Cloudflare Pages Function (`functions/share/[[id]].js`) intercepts the request
- Fetches share data from R2 storage
- Injects the data into share.html
- Returns the complete, interactive dashboard

### 3. Public Gallery
The homepage (`index.html`) displays:
- Featured shared projects
- All public shared dashboards
- Project statistics (commands, tokens, duration, cost, etc.)
- Fetches data from `/gallery-index.json` (served from R2)

### 4. Admin Dashboard
The admin interface (`admin.html`) allows authorized users to:
- View all shared projects
- Feature/unfeature projects
- Remove inappropriate content
- View share statistics
- Uses Google OAuth for authentication

## Local Development

### Testing the Gallery and Homepage
```bash
# Run the development server
python local-dev-gallery-server.py
# Visit http://localhost:8000
```

### Testing Share Viewing
```bash
# Run the share viewer server
python local-dev-share-server.py
# Visit http://localhost:4001/share/{id}
```

### Testing with Production-like Setup
```bash
# Simulates Cloudflare Pages environment
python gallery-site-server.py
# Serves both gallery (port 8000) and shares (port 4001)
```

## Deployment

### Cloudflare Pages Configuration

1. **Connect GitHub repository**

2. **Build settings:**
   ```
   Build command: cd codex-logbook-site && python build.py
   Build output directory: codex-logbook-site
   ```

3. **Environment variables:**
   ```
   ENV=PROD
   R2_ACCESS_KEY_ID=<r2-access-key-id>
   R2_SECRET_ACCESS_KEY=<r2-secret-access-key>
   R2_BUCKET_NAME=codex-logbook-shares
   R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
   GA_MEASUREMENT_ID=G-XXXXXXXXXX
   GOOGLE_CLIENT_ID=your-oauth-client-id
   GOOGLE_CLIENT_SECRET=<google-oauth-client-secret>
   ADMIN_EMAILS=admin@example.com,other@example.com
   ```

4. **Functions configuration:**
   - Functions directory: `functions`
   - The `[[id]].js` function handles dynamic share routes

### R2 Bucket Setup

1. Create bucket named `codex-logbook-shares`
2. Store share data as `{share-id}.json`
3. Store gallery index as `gallery-index.json`
4. Store share logs as `shares-log.jsonl`

## Security

- Share data is sanitized to remove sensitive paths
- Admin access requires Google OAuth + email whitelist
- Share IDs are 24-character UUIDs for uniqueness
- IP addresses in logs are SHA256 hashed for privacy

## Notes

- The Python dev servers are for local testing only
- In production, Cloudflare Pages serves all static files
- The build process ensures share viewer works standalone
- Gallery updates happen when new shares are created
