import React from 'react';
import { ArrowIcon } from '@cmsgov/design-system';

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

  return /*#__PURE__*/React.createElement(ArrowIcon, {
    title: "Caret",
    className: className,
    direction: direction
  });
};

export default Caret;