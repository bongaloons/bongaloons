import { Pose } from "../types";

export default function BongoCat({pose}: {pose: Pose}) {
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
        <div>
            <img src={poseToImage(pose)} alt="Bongo cat" />
        </div>
    )
}