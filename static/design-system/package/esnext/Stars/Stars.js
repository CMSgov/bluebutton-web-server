import React from 'react';
import { RoundedStarIcon } from '../Icons';

var Stars = function Stars(_ref) {
  var number = _ref.number,
      total = _ref.total,
      _ref$ariaHidden = _ref.ariaHidden,
      ariaHidden = _ref$ariaHidden === void 0 ? false : _ref$ariaHidden;
  var totalStars = total && number < 11 ? Math.ceil(total) : 5;
  var completeStars = Math.floor(number); // 3.5 -> 3

  var halfStar = number - completeStars !== 0; // 3.5 - 3 = 0.5, so half star exists

  var emptyStars = totalStars - completeStars - (halfStar ? 1 : 0);
  var starIcons = [];
  var starIndex = 0;

  for (var i = 0; i < completeStars; i++) {
    starIcons.push( /*#__PURE__*/React.createElement(RoundedStarIcon, {
      variation: "filled",
      key: starIndex
    }));
    starIndex++;
  }

  if (halfStar) {
    starIcons.push( /*#__PURE__*/React.createElement(RoundedStarIcon, {
      variation: "half",
      key: starIndex
    }));
    starIndex++;
  }

  for (var _i = 0; _i < emptyStars; _i++) {
    starIcons.push( /*#__PURE__*/React.createElement(RoundedStarIcon, {
      key: starIndex
    }));
    starIndex++;
  }

  return /*#__PURE__*/React.createElement("span", {
    "aria-hidden": ariaHidden,
    className: "ds-u-display--flex ds-u-flex-wrap--nowrap"
  }, starIcons);
};

export default Stars;