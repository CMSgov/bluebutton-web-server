import React from 'react';

var Card = function Card(_ref) {
  var children = _ref.children,
      className = _ref.className;
  return /*#__PURE__*/React.createElement("div", {
    className: "m-c-card ".concat(className)
  }, children);
};

export default Card;