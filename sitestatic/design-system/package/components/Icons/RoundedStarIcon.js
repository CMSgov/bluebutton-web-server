"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _propTypes = _interopRequireDefault(require("prop-types"));

var _react = _interopRequireDefault(require("react"));

var _RoundedStarFilledIcon = _interopRequireDefault(require("./RoundedStarFilledIcon"));

var _RoundedStarHalfIcon = _interopRequireDefault(require("./RoundedStarHalfIcon"));

var _RoundedStarEmptyIcon = _interopRequireDefault(require("./RoundedStarEmptyIcon"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

var RoundedStar = function RoundedStar(props) {
  if (props.variation === 'filled') {
    return /*#__PURE__*/_react.default.createElement(_RoundedStarFilledIcon.default, props);
  } else if (props.variation === 'half') {
    return /*#__PURE__*/_react.default.createElement(_RoundedStarHalfIcon.default, props);
  } else {
    return /*#__PURE__*/_react.default.createElement(_RoundedStarEmptyIcon.default, props);
  }
};

RoundedStar.propTypes = {
  className: _propTypes.default.string,
  variation: _propTypes.default.oneOf(['filled', 'half', 'empty'])
};
var _default = RoundedStar;
exports.default = _default;