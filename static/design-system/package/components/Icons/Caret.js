"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _react = _interopRequireDefault(require("react"));

var _designSystem = require("@cmsgov/design-system");

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var Caret = function Caret(_ref) {
  var className = _ref.className,
      up = _ref.up,
      left = _ref.left,
      right = _ref.right;
  console.error("[Deprecated]: Please use the <ArrowIcon /> component instead. This component will be removed in a future release.");
  var direction = 'down';

  if (up) {
    direction = 'up';
  } else if (left) {
    direction = 'left';
  } else if (right) {
    direction = 'right';
  }

  return /*#__PURE__*/_react.default.createElement(_designSystem.ArrowIcon, {
    title: "Caret",
    className: className,
    direction: direction
  });
};

var _default = Caret;
exports.default = _default;