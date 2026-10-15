# PlantPulse Digital Twin

Mobile-first industrial equipment monitoring prototype for pump P-101.

## Demo features
- Responsive phone and desktop interface
- Synthetic sample readings refresh every five seconds
- Scenario selection: normal, high vibration, low suction pressure, high bearing temperature and low flow
- Rule-based illustrative alerts and recommended checks
- Equipment details, trends, event notes and CSV exports
- Optional Supabase endpoint reachability test
- Installable Progressive Web App (PWA), with offline app shell after first successful visit

## Important limitations
All readings are generated demonstration data. This app is not connected to a real plant, PLC, SCADA, sensors or DWSIM. Thresholds and diagnosis are illustrative only and must be validated by qualified site engineers. Not for safety-critical decisions or equipment control. The prototype does not currently persist telemetry to Supabase.

## Deploy on GitHub Pages
The workflow in `.github/workflows/pages.yml` deploys this repository's root on pushes to `main`. In GitHub, open **Settings → Pages** and confirm GitHub Actions is the publishing source. Then open:
`https://yyokash16-ui.github.io/Plant-pulse/`

After opening it once online, use Microsoft Edge or Chrome's **Install PlantPulse** option to add it as a desktop app.

## Production integration path
Use an authorized industrial edge gateway to send validated sensor data through an authenticated backend API. Do not expose PLC/SCADA networks or unauthenticated control APIs to the internet. The dashboard should remain read-only for process control. Never expose a Supabase service-role key in browser code.
