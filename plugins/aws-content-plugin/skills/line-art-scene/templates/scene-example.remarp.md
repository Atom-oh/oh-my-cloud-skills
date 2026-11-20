---
remarp: true
title: "Line-art scene example"
author: "Presenter"
audience: "Cloud Engineers"
lang: en
speaker:
  name: "Presenter"
quiz: false
duration: 5
---

# Block 1: Example {timing: 5min}

:::notes
{timing: 1min}
[요약]
• This block walks one request through a small service
• Each press of Down moves the scene to the next stop
• The picture stays complete at the start, so nothing is hidden

Welcome. In this short block we follow a single request from a laptop to a table and back, one stop at a time, so that every later slide in the session can point back to this picture.
:::

---
@type: content
@fit: off
## One request, four stops

:::html

<div id="scene-request"></div>
:::

:::script
import('./common/line-art-scene/flowscene.js').then(function (m) {
  m.mount('#scene-request', {
    aria: 'A request leaves the office network, passes the API gateway and a function, and reads a table, then returns by the same path',
    H: 590, OY: 400,
    zones: [
      { box: [-0.4, 0, 0, 8.2, 5.2, 0.4], label: 'Office network', labelAt: [-0.2, 0, -1.0] },
      { box: [8.6, 0, 0, 15.6, 5.2, 0.4], label: 'AWS Region', labelAt: [8.8, 0, -1.0],
        icon: './common/aws-icons/groups/AWS-Cloud_32.svg' }
    ],
    parts: {
      laptop:  { boxes: [[1.2, 1.4, 0.4, 2.0, 1.8, 1.1]] },
      gateway: { boxes: [[10.0, 1.4, 0.4, 1.8, 1.8, 1.6]] },
      fn:      { boxes: [[14.2, 1.4, 0.4, 2.0, 2.0, 1.9]] },
      table:   { boxes: [[19.0, 1.2, 0.4, 2.6, 2.4, 2.3]] }
    },
    icons: [
      { part: 'gateway', at: [10.9, 2.3, 2.5], src: './common/aws-icons/services/Arch_Amazon-API-Gateway_48.svg' },
      { part: 'fn',      at: [15.2, 2.4, 2.8], src: './common/aws-icons/services/Arch_AWS-Lambda_48.svg' },
      { part: 'table',   at: [20.3, 2.4, 3.3], src: './common/aws-icons/services/Arch_Amazon-DynamoDB_48.svg' }
    ],
    wires: {
      req: { pts: [[3.4, 2.2, 1.4], [9.8, 2.3, 1.6], [14.0, 2.4, 1.9], [18.8, 2.4, 2.3]] }
    },
    callouts: [
      { id: 'laptop',  n: 1, anchor: [2.2, 1.4, 1.5],  at: [40, 500],  title: 'Client', sub: 'signs the request' },
      { id: 'gateway', n: 2, anchor: [10.9, 1.4, 2.0], at: [250, 130],  title: 'API gateway', sub: 'checks the caller' },
      { id: 'fn',      n: 3, anchor: [15.2, 1.4, 2.3], at: [430, 500], title: 'Function', sub: 'runs the logic' },
      { id: 'table',   n: 4, anchor: [20.3, 1.2, 2.8], at: [560, 130],  title: 'Table', sub: 'stores the result' }
    ],
    figures: [
      { at: [5.4, 0.9, 0.4], scale: 0.9, pose: 'type', busy: true, sound: 'tap tap',
        act: { send: 'type' } }
    ],
    code: ['POST /orders', 'Authorization: signed', '{ "item": "book" }'],
    overview: { label: 'OVERVIEW', title: 'One request, four stops', say: 'Press Down to follow the request.', lines: [1, 2, 3] },
    phases: [
      { key: 'send',  label: 'STEP 1', title: 'The client sends it', say: 'The request leaves the office <b>signed</b>.',
        focus: ['laptop'], badge: 'laptop', packet: { wire: 'req', span: [0, 1] }, lines: [1, 2] },
      { key: 'gate',  label: 'STEP 2', title: 'The gateway checks it', say: 'Only a valid caller gets through.',
        focus: ['gateway'], badge: 'gateway', packet: { wire: 'req', span: [1, 2], mode: 'wait' }, lines: [2] },
      { key: 'run',   label: 'STEP 3', title: 'The function runs', say: 'The logic reads the body and decides.',
        focus: ['fn'], badge: 'fn', packet: { wire: 'req', span: [2, 3] }, lines: [3] },
      { key: 'store', label: 'STEP 4', title: 'The table answers', say: 'The answer goes back the same way.',
        focus: ['table'], badge: 'table', packet: { wire: 'req', span: [3, 0], mode: 'pingpong' }, lines: [3] }
    ]
  });
});
:::

:::notes
{timing: 2min}
[요약]
• A request leaves the client signed
• The gateway checks the caller, the function runs the logic, the table answers
• The answer returns by the same path

Let me walk one request through this picture, because it makes the rest of the session easier to follow. The client signs it and sends it out.↓ The gateway is the front door, and it only lets valid callers through.↓ Then the function runs, and it is the part you will write yourself.↓ Finally the table answers, and the response comes back the way it went.↓
:::
