import { Pose } from "../types";

export default function BongoCat({pose, overlay = undefined}: {pose: Pose, overlay?: string | undefined}) {
    function poseToImage(pose: Pose) {
        if (pose === "idle") {
            return "/bongo_11.png";
        }
        if (pose === "left") {
            return "/bongo_01.png";
        }
        if (pose === "right") {
            return "/bongo_10.png";
        }
        if (pose === "both") {
            return "/bongo_00.png";
        }
        return "/bongo_11.png";
    }
    return (
        <div className="relative">
            <img src={poseToImage(pose)} alt="Bongo cat"  />
            {overlay && <img src={overlay} alt="Bongo cat overlay" className="absolute top-0 left-0"/>}
        </div>
    )
}