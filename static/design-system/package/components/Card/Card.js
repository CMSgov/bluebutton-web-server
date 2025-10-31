"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _react = _interopRequireDefault(require("react"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var Card = function Card(_ref) {
  var children = _ref.children,
      className = _ref.className;
  return /*#__PURE__*/_react.default.createElement("div", {
    className: "m-c-card ".concat(className)
  }, children);
};

var _default = Card;
exports.default = _default;