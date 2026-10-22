const React = window.React;
const ReactDOM = window.ReactDOM;
const htm = window.htm;

if (!htm) {
  console.error('htm.umd.js not loaded');
}

export const html = htm.bind(React.createElement);
