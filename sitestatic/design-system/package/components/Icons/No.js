"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _react = _interopRequireDefault(require("react"));

var _designSystem = require("@cmsgov/design-system");

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var No = function No(_ref) {
  var _ref$className = _ref.className,
      className = _ref$className === void 0 ? '' : _ref$className;
  console.error("[Deprecated]: Please use the <CloseIcon /> component with 'ds-c-icon-color--error' CSS class instead. This component will be removed in a future release.");
  return /*#__PURE__*/_react.default.createElement(_designSystem.CloseIcon, {
    title: "Caret",
    className: "ds-c-icon-color--error ".concat(className)
  });
};

var _default = No;
exports.default = _default;