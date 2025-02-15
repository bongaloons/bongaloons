import { useContext } from "react";
import { Pose } from "../types";
import { GameContext } from "../context/GameContext";

export default function BongoCat() {
    const { gameState } = useContext(GameContext);

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
            <img src={poseToImage(gameState.currentPose)} className="mx-auto max-w-[400px]" alt="Bongo cat" />
        </div>
    )
}