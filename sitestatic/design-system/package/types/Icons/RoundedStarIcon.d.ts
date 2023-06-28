import { IconCommonProps } from '@cmsgov/design-system/dist/components/Icons/SvgIcon';
export declare type RoundedStarVariation = 'filled' | 'half' | 'empty';
export interface RoundedStarProps extends IconCommonProps {
    className?: string;
    variation?: RoundedStarVariation;
}
declare const RoundedStar: (props: RoundedStarProps) => JSX.Element;
export default RoundedStar;
