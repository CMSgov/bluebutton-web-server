"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _react = _interopRequireDefault(require("react"));

var _designSystem = require("@cmsgov/design-system");

var _InfoCircleOutlineIcon = _interopRequireDefault(require("../Icons/InfoCircleOutlineIcon"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

_designSystem.HelpDrawerToggle.defaultProps = {
  icon: /*#__PURE__*/_react.default.createElement(_InfoCircleOutlineIcon.default, null)
};
var _default = _designSystem.HelpDrawerToggle;
exports.default = _default;