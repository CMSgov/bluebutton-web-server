"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _react = _interopRequireDefault(require("react"));

var _designSystem = require("@cmsgov/design-system");

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var Close = function Close(_ref) {
  var className = _ref.className;
  console.error("[Deprecated]: Please use the <CloseIconThin /> component with 'ds-c-icon-color--error' CSS class instead. This component will be removed in a future release.");
  return /*#__PURE__*/_react.default.createElement(_designSystem.CloseIconThin, {
    className: className
  });
};

var _default = Close;
exports.default = _default;