"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _react = _interopRequireDefault(require("react"));

var _classnames = _interopRequireDefault(require("classnames"));

var _designSystem = require("@cmsgov/design-system");

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

var defaultProps = {
  className: '',
  title: 'Filled Star'
};

var RoundedStarHalfIcon = function RoundedStarHalfIcon(props) {
  var iconCssClasses = (0, _classnames.default)('ds-c-icon--rounded-star', 'ds-c-icon--rounded-star-filled', props.className);
  return /*#__PURE__*/_react.default.createElement(_designSystem.SvgIcon, _extends({}, defaultProps, props, {
    className: iconCssClasses
  }), /*#__PURE__*/_react.default.createElement("g", null, /*#__PURE__*/_react.default.createElement("polygon", {
    fillRule: "evenodd",
    clipRule: "evenodd",
    fill: "currentColor",
    points: "12.5,17.5 18.4,21 16.8,14.3 22,9.9 15.2,9.3 12.5,3 9.8,9.3 3,9.9 8.2,14.3 6.6,21"
  }), /*#__PURE__*/_react.default.createElement("path", {
    className: "FilledStarPath",
    fillRule: "evenodd",
    clipRule: "evenodd",
    fill: "currentColor",
    d: "M11.5,3.6L9.2,8.3L4,9C3,9.2,2.7,10.3,3.3,10.9l3.8,3.6l-0.9,5.1c-0.2,0.9,0.8,1.6,1.6,1.2 l4.6-2.4l4.6,2.4c0.8,0.4,1.8-0.3,1.6-1.2l-0.9-5.1l3.8-3.6C22.3,10.3,22,9.2,21,9l-5.2-0.7l-2.3-4.7C13.1,2.8,11.9,2.8,11.5,3.6z"
  })));
};

var _default = RoundedStarHalfIcon;
exports.default = _default;