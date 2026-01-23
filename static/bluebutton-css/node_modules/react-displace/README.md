# react-displace [![Build Status](https://travis-ci.org/davidtheclark/react-displace.svg?branch=master)](https://travis-ci.org/davidtheclark/react-displace)

A higher-order component that displaces *your* component into a remote region of the DOM. When your component mounts, it renders to the end of `document.body` (or into any specified DOM node), instead of its expected place within the React component tree; but it still maintains its normal life cycle within the tree, mounting, updating, and unmounting as expected.

This is useful when the HTML source order enforced by React's component tree won't serve your purposes. For example: if initialization and props for a modal or an obstructive overlay (e.g. "Loading...") will come from some component deeply nested within you app, but you want to render the modal or overlay as a direct child of `document.body` so that you can easily `position` it and set its `z-index`.

[Check out the demo.](http://davidtheclark.github.io/react-displace/demo/)

## Installation

```
npm install react-displace
```

You'll need to be using a bundler like Browserify, Webpack, or Rollup.

`dist/displace.js` is the Babel-compiled code that you will use.

### React Dependency

Version 2.3+ uses React 16's [Portals](https://reactjs.org/docs/portals.html), if available.
If not, it resorts to the old ways, so is still compatible with previous versions of React.

Version 2+ is compatible with React >=0.14.x.

Version 1+ is compatible with React 0.13.x.

## Tested Browser Support

IE9+.

## Usage

react-displace is a ["higher-order component"](https://facebook.github.io/react/docs/higher-order-components.html): a function that takes your component as an argument and returns a new component that includes your component wrapped in some special functionality.

It has a simple signature:

```js
const DisplacedComponent = displace(YourComponent[, options]);
```

### Options

#### renderTo

Type: DOM node or string selector

By default, the displaced component is appended to a new `<div>` attached directly to `document.body`. If instead you would like to specify a node that the component should be displaced to, do that with `renderTo`.

If `renderTo` is a DOM node, the displaced component will be rendered there.

If `renderTo` is a selector string, it is passed to `document.querySelector()`, and the displaced component will be rendered to that result.

### Example

```js
const React = require('react');
const displace = require('react-displace');

class Foo extends React.Component { .. }

const FooDisplacedToBody = displace(Foo);
const FooDisplacedToBar = displace(Foo, document.getElementById('bar'));
const FooDisplacedToBaz = displace(Foo, '#baz');
```

In the example above, you can use any `FooDisplacedTo*` exactly as you would use `Foo`; and any `props` you provide to `FooDisplacedTo*` will be passed through to its internal `Foo` component. (e.g. If `Foo` has a `prop` called `severity`, so does `FooDisplacedTo*`.)

The only differences are that all of the `FooDisplacedTo*` components will be rendered to some special place in the DOM, instead of being inserted wherever it is used within the React component tree.
- `FooDisplacedToBody` will be rendered into a new `<div>` appended directly to `document.body`,
- `FooDisplacedToBar` and `FooDisplacedToBaz` will be appended into their designated containers.

The `FooDisplacedTo*` components will also have an additional `prop`: `mounted`. The `mounted` prop can be used to declare whether the component should be rendered or not — which can also be done by actually mounting and unmounting the component.

So let's say you have the following HTML:

```html
<div id="app-container"></div>
<div id="bar"></div>
<div id="baz"></div>
```

And you have something like the following JS:

```js
const React = require('react');
const displace = require('react-displace');

class Foo extends React.Component { .. }

const FooDisplacedToBody = displace(Foo);
const FooDisplacedToBar = displace(Foo, document.getElementById('bar'));
const FooDisplacedToBaz = displace(Foo, '#baz');

class App extends React.Component {
  render() {
    return (
      <div id="rendered-app">
        <Foo text='in my normal place' />
        <FooDisplacedToBody text='displaced to body' />
        <FooDisplacedToBar text='displaced to bar' />
        <FooDisplacedToBaz text='displaced to baz' />
      </div>
    );
  },
}
```

What ends up rendering should look something like this:

```html
<div id="app-container">
  <div id="rendered-app">
    <div>in my normal place</div>
  </div>
</div>
<div id="bar">
  <div>displaced to bar</div>
</div>
<div id="baz">
  <div>displaced to baz</div>
</div>
<div>
  <div>displaced to body</div>
</div>
```

## `DisplacedComponent.WrappedComponent`

The component that you pass to `displace()` is available on the class it returns as the static property `WrappedComponent`.

```js
class MyComponent extends React.Component { .. }
const MyComponentDisplaced = displace(MyComponent);
MyComponentDisplaced.WrappedComponent === MyComponent; // true
```

## Contributing & Development

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

Lint with `npm run lint`.

Test with `npm run jest`.

## Questions with Answers

- **Will my displaced element understand the `context` from its React element tree?** Yes!

## Caveats

- If there is no `document` (e.g. using `ReactDOMServer.renderToString()` server-side), this thing won't work,
  so it just returns a component that renders nothing. You'll have to initiate it when there is a `document`.
