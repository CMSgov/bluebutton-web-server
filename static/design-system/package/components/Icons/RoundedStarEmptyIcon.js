"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _react = _interopRequireDefault(require("react"));

var _classnames = _interopRequireDefault(require("classnames"));

var _uniqueId = _interopRequireDefault(require("lodash/uniqueId"));

var _designSystem = require("@cmsgov/design-system");

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

var defaultProps = {
  className: '',
  title: 'Empty Star'
};

var RoundedStarEmptyIcon = function RoundedStarEmptyIcon(props) {
  var clipPath1 = (0, _uniqueId.default)('empty_clip_path_');
  var clipPath2 = (0, _uniqueId.default)('empty_clip_path_');
  var clipPath3 = (0, _uniqueId.default)('empty_clip_path_');
  var iconCssClasses = (0, _classnames.default)('ds-c-icon--rounded-star', 'ds-c-icon--rounded-star-empty', props.className);
  return /*#__PURE__*/_react.default.createElement(_designSystem.SvgIcon, _extends({}, defaultProps, props, {
    className: iconCssClasses
  }), /*#__PURE__*/_react.default.createElement("clipPath", {
    id: clipPath1
  }, /*#__PURE__*/_react.default.createElement("path", {
    d: "M11,3.6L8.8,8.3L3.9,9C3,9.2,2.7,10.3,3.3,10.9l3.6,3.6L6,19.7c-0.2,0.9,0.8,1.6,1.6,1.2l4.4-2.4l4.4,2.4 c0.8,0.4,1.7-0.3,1.6-1.2l-0.8-5.1l3.6-3.6c0.6-0.7,0.3-1.8-0.6-1.9l-4.9-0.7L13,3.6C12.6,2.8,11.4,2.8,11,3.6z"
  })), /*#__PURE__*/_react.default.createElement("clipPath", {
    id: clipPath2
  }, /*#__PURE__*/_react.default.createElement("rect", {
    x: "-8",
    y: "-8",
    width: "40",
    height: "40"
  })), /*#__PURE__*/_react.default.createElement("clipPath", {
    id: clipPath3
  }, /*#__PURE__*/_react.default.createElement("rect", {
    x: "3",
    y: "3",
    width: "18",
    height: "18"
  })), /*#__PURE__*/_react.default.createElement("g", {
    clipPath: "url(#".concat(clipPath1, ")")
  }, /*#__PURE__*/_react.default.createElement("g", {
    clipPath: "url(#".concat(clipPath2, ")"),
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeMiterlimit: 10
  }, /*#__PURE__*/_react.default.createElement("path", {
    className: "EmptyStarPath",
    clipPath: "url(#".concat(clipPath3, ")"),
    d: "M11,3.6L8.8,8.3L3.9,9C3,9.2,2.7,10.3,3.3,10.9l3.6,3.6L6,19.7c-0.2,0.9,0.8,1.6,1.6,1.2l4.4-2.4l4.4,2.4 c0.8,0.4,1.7-0.3,1.6-1.2l-0.8-5.1l3.6-3.6c0.6-0.7,0.3-1.8-0.6-1.9l-4.9-0.7L13,3.6C12.6,2.8,11.4,2.8,11,3.6z"
  }))));
};

var _default = RoundedStarEmptyIcon;
exports.default = _default;