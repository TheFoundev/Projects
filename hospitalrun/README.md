# HospitalRun

Patient records that work offline

> Offline-first hospital management frontend covering patient records, appointments, prescriptions, labs, imaging and incidents.

## Overview

An original, self-contained implementation of the **HospitalRun** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Patient registry with allergies and blood type
- Appointment scheduling by department and provider
- Prescriptions with dosage and status
- Lab orders with priority and results
- Incident log for clinical safety events

## Stack

`React; Node.js; PouchDB; CouchDB`

The app intentionally keeps a dependency-free Node stack; SQLite is provided by Node's built-in `node:sqlite` module (Node 22.5+).

## Run

```bash
npm start
# open http://localhost:3000
npm test
```

## Structure

```text
hospitalrun/
├── server.js          HTTP API, auth and SQLite schema
├── config.json        domain model and seed data
├── public/            dependency-free single-page client
├── test/smoke.test.js API smoke test
└── data/app.db        local database (gitignored)
```

## Testing

```bash
npm test
```

28 tests: the clinical rules on their own (the overlap check, the double
booking rules for a patient and for a provider, the prescription and lab order
checks, the state machines, the blood types, the severities, the patient
alerts and the day schedule) and the API on a real server (a patient with the
configured defaults, an impossible blood type, an appointment for a patient
that does not exist, a patient booked twice, a prescription without a dose, a
lab order moving through its states, the patient summary, the clinic diary
and the severity of an incident).

## The clinical domain

`clinical.js` holds the rules, as pure functions:

- a patient cannot be booked twice and a provider cannot be in two places at
  once, and a cancelled appointment blocks nothing
- a prescription needs a patient who is active, a medication and a dose
- a lab order needs a patient who is active, a test and a known priority, and
  it moves through `ordered`, `collected`, `in_progress`, `completed`
- a patient record raises alerts for an allergy, an unknown blood type and a
  missing one
- an incident is graded by severity and the severity says what has to happen
- the clinic diary of a day and the summary of one patient

The API adds `/api/patients/:id/summary`, `/api/schedule`,
`/api/appointments/:id/status`, `/api/lab_orders/:id/status`,
`/api/prescriptions/:id/status`, `/api/incidents/:id/status` and
`/api/incidents/:id/severity`, and the clinical rules run before any of the
five records is created.

## Notes and limitations

- The upstream project is an offline-first PouchDB/CouchDB client; this MVP stores records in local SQLite and documents the sync boundary instead of pretending to replicate it.
- It is a demo and must not be used for real clinical decisions.
- The UI is responsive and works on tablets, matching the ward-round use case.

## License

MIT. See `LICENSE`.
