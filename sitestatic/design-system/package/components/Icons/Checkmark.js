"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _react = _interopRequireDefault(require("react"));

var _designSystem = require("@cmsgov/design-system");

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var Checkmark = function Checkmark(_ref) {
  var className = _ref.className;
  console.error("[Deprecated]: Please use the <CheckIcon /> component with 'ds-c-icon-color--primary' CSS class instead. This component will be removed in a future release.");
  return /*#__PURE__*/_react.default.createElement(_designSystem.CheckIcon, {
    className: "ds-c-icon-color--primary ".concat(className)
  });
};

var _default = Checkmark;
exports.default = _default;